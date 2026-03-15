"""
RG Capital daily review email flow.

1. Reads fund POV artifacts from RG_Capital
2. Composes a summary email with key metrics and questions
3. Sends to Roman
4. When Roman replies, converts his response to a claude -p prompt
5. Runs the prompt against RG_Capital
6. Emails back the results
"""

import json
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path
from textwrap import dedent

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.email_client import EmailClient

RG_ROOT = Path("/home/roman/RG_Capital")


def load_profile() -> dict:
    with open("config/profile.yaml") as f:
        return yaml.safe_load(f)


def load_fund_povs() -> dict[str, dict]:
    """Load all fund POV artifacts from RG_Capital."""
    pov_dir = RG_ROOT / "org" / "artifacts" / "fund_pov"
    povs = {}
    if pov_dir.exists():
        for f in pov_dir.glob("*_pov.json"):
            fund_name = f.stem.replace("_pov", "")
            povs[fund_name] = json.loads(f.read_text())
    return povs


def compose_review_email(target_date: date) -> tuple[str, str]:
    """Compose the daily review email. Returns (subject, body)."""
    povs = load_fund_povs()

    subject = f"RG Capital Daily Review — {target_date.strftime('%A %b %d')}"

    sections = []
    questions = []

    # Delta One
    if "delta_one" in povs:
        d1 = povs["delta_one"]
        rec = d1.get("recommendation", {})
        sections.append(dedent(f"""\
            DELTA ONE
            Direction: {d1.get('direction', 'N/A')} | Regime: {d1.get('regime', 'N/A')}
            BTC Close: ${d1.get('btc_close', 0):,.2f}
            Position: {rec.get('position', 'N/A')} ({rec.get('instrument', '')})
            Vol Regime: {d1.get('vol_regime', 'N/A')} | Dealer Gamma: {d1.get('dealer_gamma', 'N/A')}
            Vol Fund Note: {d1.get('vol_fund', '')}
            LS Fund Note: {d1.get('ls_fund', '')}"""))

        if rec.get("position") == "FLAT":
            questions.append("Delta One is FLAT — any conviction to enter a position or stay sidelined?")

    # Vol Fund
    if "vol_fund" in povs:
        vf = povs["vol_fund"]
        best = vf.get("best_strategy", {})
        sections.append(dedent(f"""\
            VOL FUND
            Status: {vf.get('promote_status', 'N/A')} | Cycle: {vf.get('cycle', 'N/A')}
            Best Strategy: {best.get('type', 'N/A')} on {best.get('symbols', 'N/A')}
            OOS Sharpe: {best.get('oos_sharpe_test', 'N/A')}
            Regime: {vf.get('regime', '')}
            Next: {', '.join(vf.get('next_priorities', []))}
            Blocked: {', '.join(vf.get('blocked_hypotheses', []))}"""))

        if best.get("live_gate_passed"):
            questions.append(f"Vol Fund short_call passed live gate (Sharpe {best.get('oos_sharpe_test')}). Ready to allocate capital?")

    # LS Fund
    if "ls_fund" in povs:
        ls = povs["ls_fund"]
        candidates = ls.get("short_book_candidates", {})
        long_cands = ls.get("long_book_candidates", {})

        top_shorts = candidates.get("full_scoring_top_10", [])[:5]
        short_str = ", ".join(f"{s['ticker']} ({s['short_conviction']:.1f})" for s in top_shorts)

        top_longs = long_cands.get("top_5", [])[:5]
        long_str = ", ".join(f"{l['ticker']} ({l['long_conviction']:.1f})" for l in top_longs)

        fraud_alerts = candidates.get("fraud_alerts", "None")

        sections.append(dedent(f"""\
            LS FUND
            Posture: {ls.get('posture', 'N/A')} | BTC Regime: {ls.get('btc_regime', 'N/A')}
            Active Signals: {', '.join(ls.get('active_signals', []))}
            Top Short Candidates: {short_str}
            Top Long Candidates: {long_str}
            Conviction Gap: {candidates.get('conviction_gap', 'N/A')}
            Fraud Alerts: {fraud_alerts}
            Data Health: {ls.get('data_health', 'N/A')}"""))

        if candidates.get("conviction_gap"):
            questions.append("LS Fund: No short hits 6.0 conviction yet. Want to lower threshold or wait for valuation data?")

        if "fraud" in str(fraud_alerts).lower():
            questions.append(f"Fraud flags raised: {fraud_alerts[:200]}. Investigate further?")

    # Compose body
    body = f"RG CAPITAL — {target_date.strftime('%A, %B %d %Y')}\n"
    body += "=" * 50 + "\n\n"

    for section in sections:
        body += section + "\n\n" + "-" * 40 + "\n\n"

    if questions:
        body += "QUESTIONS FOR YOU:\n\n"
        for i, q in enumerate(questions, 1):
            body += f"  {i}. {q}\n"
        body += "\n"

    body += dedent("""\
        ---
        Reply to this email with any asks. Examples:
        - "Run the vol fund backtest with 3% OTM instead of 5%"
        - "Add COIN to the LS fund universe"
        - "Show me the PnL curve for delta_one last 30 days"
        - "What's blocking the LETF arb strategy?"

        Your reply will be executed as a task against RG_Capital and you'll get the results back.
    """)

    return subject, body


def send_review(target_date: date = None, dry_run: bool = False) -> str:
    """Send the daily review email."""
    if target_date is None:
        target_date = date.today()

    profile = load_profile()
    subject, body = compose_review_email(target_date)

    if dry_run:
        return f"Subject: {subject}\n\n{body}"

    google_cfg = profile["google"]
    email_client = EmailClient(
        credentials_path=google_cfg["credentials_path"],
        token_path=google_cfg["token_path"],
    )
    email_client.authenticate()

    result = email_client.send_email(
        to=email_client.user_email,
        subject=subject,
        body=body,
    )

    # Save thread ID for reply tracking
    thread_file = Path("data/review_threads.json")
    thread_file.parent.mkdir(parents=True, exist_ok=True)
    threads = {}
    if thread_file.exists():
        threads = json.loads(thread_file.read_text())
    threads[target_date.isoformat()] = {
        "thread_id": result.get("threadId"),
        "message_id": result.get("id"),
        "sent_at": datetime.now().isoformat(),
    }
    thread_file.write_text(json.dumps(threads, indent=2))

    return f"Review email sent for {target_date} (thread: {result.get('threadId')})"


def process_replies() -> list[str]:
    """
    Check for replies to review emails, convert to claude -p prompts,
    run them, and email back results.
    """
    profile = load_profile()
    google_cfg = profile["google"]

    email_client = EmailClient(
        credentials_path=google_cfg["credentials_path"],
        token_path=google_cfg["token_path"],
    )
    email_client.authenticate()

    # Find replies to RG Capital review emails
    replies = email_client.find_replies("RG Capital Daily Review")

    # Load tracked threads
    thread_file = Path("data/review_threads.json")
    if not thread_file.exists():
        return ["No review threads found"]

    threads = json.loads(thread_file.read_text())
    tracked_thread_ids = {v["thread_id"] for v in threads.values()}

    # Load already-processed message IDs
    processed_file = Path("data/processed_replies.json")
    processed = set()
    if processed_file.exists():
        processed = set(json.loads(processed_file.read_text()))

    results = []

    for reply in replies:
        # Skip if not in a tracked thread or already processed
        if reply["threadId"] not in tracked_thread_ids:
            continue
        if reply["id"] in processed:
            continue

        # Extract the reply text (strip quoted content)
        reply_body = _strip_quoted_text(reply["body"])
        if not reply_body.strip():
            continue

        # Convert reply to a claude prompt
        prompt = _reply_to_prompt(reply_body)

        # Run claude -p against RG_Capital
        output = _run_claude_prompt(prompt)

        # Email back the results
        result_subject = f"Re: {reply['subject']} — Task Complete"
        result_body = f"YOUR ASK:\n{reply_body.strip()}\n\n"
        result_body += "=" * 50 + "\n\n"
        result_body += f"RESULT:\n{output}\n\n"
        result_body += "---\nReply again with follow-up asks or new tasks."

        email_client.send_email(
            to=email_client.user_email,
            subject=result_subject,
            body=result_body,
            thread_id=reply["threadId"],
        )

        # Mark as processed
        processed.add(reply["id"])
        email_client.mark_as_read(reply["id"])

        results.append(f"Processed reply: {reply_body[:80]}...")

    # Save processed state
    processed_file.parent.mkdir(parents=True, exist_ok=True)
    processed_file.write_text(json.dumps(list(processed), indent=2))

    return results if results else ["No new replies to process"]


def _strip_quoted_text(body: str) -> str:
    """Remove quoted reply text (lines starting with >)."""
    lines = body.split("\n")
    clean = []
    for line in lines:
        # Stop at quoted text or signature markers
        if line.startswith(">") or line.strip() == "--" or "wrote:" in line:
            break
        clean.append(line)
    return "\n".join(clean)


def _reply_to_prompt(reply_text: str) -> str:
    """Convert Roman's reply into a well-structured claude -p prompt."""
    return dedent(f"""\
        You are working on the RG_Capital programmatic trading project at /home/roman/RG_Capital.
        Read the CLAUDE.md file first to understand the project structure and conventions.

        Roman (the project owner) has the following ask:

        ---
        {reply_text.strip()}
        ---

        Execute this task. Follow the project's conventions in CLAUDE.md.
        If this requires code changes, make them.
        If this requires analysis, provide it with specific numbers and data.
        If this requires running a backtest or query, do it and show results.

        Be thorough but concise. Show your work.
    """)


def _run_claude_prompt(prompt: str) -> str:
    """Run a claude -p prompt against RG_Capital and return the output."""
    try:
        result = subprocess.run(
            ["claude", "-p", prompt, "--allowedTools", "Read,Glob,Grep,Bash,Edit,Write"],
            capture_output=True,
            text=True,
            timeout=300,  # 5 min max
            cwd=str(RG_ROOT),
        )
        output = result.stdout
        if result.returncode != 0 and result.stderr:
            output += f"\n\nSTDERR:\n{result.stderr}"
        return output if output else "No output produced."
    except subprocess.TimeoutExpired:
        return "Task timed out after 5 minutes. May need manual intervention."
    except FileNotFoundError:
        return "claude CLI not found. Make sure it's installed and in PATH."


def main():
    import argparse

    parser = argparse.ArgumentParser(description="RG Capital review email system")
    parser.add_argument("action", choices=["send", "check", "dry-run"],
                       help="send=send review email, check=process replies, dry-run=preview email")
    parser.add_argument("--date", type=str, help="Date (YYYY-MM-DD)")
    args = parser.parse_args()

    if args.action == "dry-run":
        target = date.fromisoformat(args.date) if args.date else date.today()
        print(send_review(target, dry_run=True))
    elif args.action == "send":
        target = date.fromisoformat(args.date) if args.date else date.today()
        print(send_review(target))
    elif args.action == "check":
        results = process_replies()
        for r in results:
            print(r)


if __name__ == "__main__":
    main()
