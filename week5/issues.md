# Issues Found and Fixed: `loan_calculator.py`

**Student:** Naveen Karthikeyan (PES2UG24CS306), Section 5E
**Repo:** L5_57_loan-eligibility

Line numbers refer to the **original** file. Severity uses Bandit's rating for security issues and my own judgement for logic bugs.

## Summary

| Tool | Before | After |
|------|--------|-------|
| Pylint | 5.17 / 10 | **10.00 / 10** |
| Bandit | 8 issues (2 High, 1 Medium, 5 Low) | **0 issues** |
| Flake8 | 22 issues | **0 issues** |

## Security issues (Bandit)

| Issue | Type | Line(s) | Description | Fix Approach |
|-------|------|---------|-------------|--------------|
| Insecure FTP (B402, B321) | Security, **High** | 3, 68–71 | Loan reports were uploaded over plain FTP, so the reports and login credentials crossed the network unencrypted (CWE-319). | Removed `ftplib`. The upload now uses `http.client.HTTPSConnection` with `ssl.create_default_context()`, which encrypts the connection and checks the server's certificate. |
| Unsafe deserialisation with `marshal` (B302) | Security, **Medium** | 4, 57, 64 | `marshal.loads` on a file from disk can crash or misbehave on a tampered file, and marshal is not meant for storing data long-term (CWE-502). | Replaced with `json.dump` / `json.load`. The data file changed from `loans.bin` to `loans.json`. |
| Hardcoded password (B107) | Security, Low | 67 | Bureau password `"Bureau#2024"` was hard-coded as a default argument, so anyone who can read the source has it (CWE-259). | Removed the parameters. A token is read from the `BUREAU_API_TOKEN` environment variable, and the function fails with a clear error if it isn't set. |
| Weak random for IDs (B311) | Security, Low | 51 | `random.randint` is predictable, so application IDs could be guessed (CWE-330). | Used `secrets.randbelow`, which is cryptographically secure. |
| Shelling out to `mail` (B404, B603, B607) | Security, Low | 6, 74 | `subprocess.run(["mail", ...])` ran an executable found on PATH by its partial name with an applicant-supplied email address (CWE-78), and didn't check whether it succeeded. | Replaced with `smtplib.SMTP_SSL` and `email.message.EmailMessage`. No external process is started any more. |

## Logic bugs (found by running the program; no tool flagged most of these)

| Issue | Type | Line(s) | Description | Fix Approach |
|-------|------|---------|-------------|--------------|
| Rate passed as percentage | Bug, **High** | 94 | `calculateEMI(500000, 9, 5)` used 9 (900%) instead of 0.09. The demo printed an EMI of ₹3,75,000/month on a ₹5L loan. | Demo now passes `0.09`, which gives an EMI of ₹10,379.18. Docstring states the rate is a fraction. |
| Eligibility shortcut bypasses checks | Bug, **High** | 24–25 | `credit_score > 750 or income > 25000` returned `True` before the FOIR and loan-type checks ran. An applicant spending 80% of income on EMIs was approved, and so was the loan type `"crypto"`. | Removed the shortcut. Now age, FOIR (≤ 50%), loan type (`in VALID_LOAN_TYPES`) and minimum credit score (`MIN_CREDIT_SCORE = 650`) must **all** pass. Both demo cases now correctly return `False`. |
| Max loan ignores interest | Bug, **High** | 33–38 | Max loan was just affordable EMI × months (₹9,00,000). `annual_rate` was never used (Pylint W0613 hinted at this). | Used the present value of an annuity: `A·((1+r)^n − 1)/(r(1+r)^n)`, which gives ₹7,22,600.60. Returns 0 if no EMI capacity is left. |
| Interest saved includes principal | Bug, Medium | 76–79 | Comparing total payments counted the ₹50,000 prepayment itself as "interest saved" (₹62,275). | Subtracted the prepayment, so only interest is counted: ₹12,275.07. |
| Risk band accepts impossible scores | Bug, Medium | 81–91 | Credit scores run from 300 to 900, but 950 was rated `"LOW"` risk. | Scores above 900 or below 300 now return `"INVALID"`. |
| Division by zero | Bug, Medium | 15–17, 26 | A 0% rate crashed `calculateEMI`, and `income = 0` crashed `checkEligibility`. | Added a 0% branch (`principal / n`) and an `income <= 0` guard. |
| Loan book overwritten each run | Bug, Low | 53–58 | `saveApplication` wrote only the in-memory records, which wiped earlier applications from the file. | Load existing records before saving. |

## Quality and style issues (Pylint, Flake8)

| Issue | Type | Line(s) | Description | Fix Approach |
|-------|------|---------|-------------|--------------|
| Mutable default arg (W0102) | Bug, **Medium** | 20–21 | `history=[]` is created once and shared by every call, so it kept growing across calls. It was never read. | Removed the parameter. (The general fix is `history=None` and creating the list inside the function.) |
| Files not closed safely (R1732) | Quality, Medium | 56, 63, 70 | `open()` without `with`. The FTP upload never closed its file at all. | Used `with open(...)` everywhere. The HTTPS connection is closed in a `finally` block. |
| `global` statement (W0603) | Quality, Low | 62 | `loadApplications` rebound the module global. | `applications.clear()` then `.update(records)` changes the dict in place, so no `global` is needed. |
| Shadowing built-in, unused variable (W0622, W0612) | Quality, Low | 34, 36 | `sum` hid the built-in, and `month` was unused. | Removed when `max_loan_amount` was rewritten. |
| Naming and docstrings (C0103, C0114, C0116) | Style, Low | all functions | camelCase function names and no docstrings. | Renamed to snake_case (`calculate_emi`, `check_eligibility`, ...) and added module and function docstrings. |
| Redundant control flow (R1705, R1703, R1714, C0325) | Style, Low | 28–31, 79, 82–91 | `else` after `return`, chained `==` comparisons, and brackets around a return value. | Used `loan_type not in VALID_LOAN_TYPES`, flat `if` returns, and removed the brackets. |
| Unused import, empty f-string (F401/W0611, F541/W1309) | Style, Low | 2, 104 | `math` was never used, and `f"..."` had no placeholders. | Removed the import and made it a plain string. |
| Demo runs on import | Quality, Low | 106 | A bare `main()` call ran the demo and wrote `loans.json` whenever the module was imported. | Wrapped it in `if __name__ == "__main__":`. |
| Blank lines (E302, E305) | Style, Low | 14–106 | One blank line between top-level functions; PEP 8 requires two. | Added two blank lines around each top-level definition. |
| Line too long (E501, C0301) | Style, Low | 20, 55, 70, 78, 95, 96, 100 | Lines longer than 79 characters. | Wrapped dict literals, call arguments and docstrings, and split expressions into named variables. |

## Demo output: before vs after

| Line | Before | After |
|------|--------|-------|
| EMI for 5L @ 9% for 5 years | 375000.000000001 | 10379.18 |
| Eligible (score 760, income 15000, EMIs 12000) | True | False (80% FOIR) |
| Eligible (unknown loan type 'crypto') | True | False |
| Max loan for income 40000 | 900000.0 | 722600.6 |
| Risk band for 950 | LOW | INVALID |
| Interest saved by prepaying 50000 | 62275.07 | 12275.07 |

## Commits

1. Add baseline Pylint, Bandit and Flake8 reports (before fixes)
2. Fix all Bandit security findings
3. Fix calculation and eligibility logic bugs found in demo output
4. Fix Pylint findings (5.17 → 10.00/10)
5. Fix all Flake8 (PEP 8) findings
6. Add issue table, reflection and after reports
