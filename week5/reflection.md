# Reflection: Lab 5 Static Code Analysis

**Student:** Naveen Karthikeyan (PES2UG24CS306), Section 5E

### 1. Which issues were the easiest to fix, and which were the hardest? Why?

The easiest were the Flake8 and Pylint style issues: missing blank lines, long lines, an unused `import math`, an f-string with no placeholders, and camelCase names. Each warning names the exact line and the fix is mechanical. The `random` → `secrets` and `marshal` → `json` swaps were also quick, because the safer module is a drop-in replacement.

The hardest were the issues where removing the warning wasn't enough on its own:

- **FTP (B402/B321, High).** I first tried switching to `ftplib.FTP_TLS`, but Bandit flags *any* import of `ftplib`. I had to change the upload to HTTPS with `http.client.HTTPSConnection` and a verified SSL context, and move the hardcoded password into an environment variable.
- **The logic bugs.** No tool reported that the EMI was ₹3,75,000 on a ₹5L loan, that an applicant spending 80% of their income on EMIs was "eligible", or that a credit score of 950 was "LOW" risk. Each one took reasoning about what a bank would expect, and in two cases a new formula (present value of an annuity for the maximum loan; subtracting the prepaid principal for interest saved). Pylint did give one clue: `annual_rate` was an unused argument in `maxLoanAmount`, which is what exposed that the function ignored interest.

### 2. Did the static analysis tools report any false positives? If so, describe one example.

Not strictly, but a few warnings flag a *risk* rather than a definite bug, so whether they matter depends on context:

- **B404 (`import subprocess`)** is reported just for importing the module. `subprocess.run([...])` with a list and no `shell=True` is not open to shell injection. In this file, though, it ran `mail` by partial path with user-controlled input, so the warning was worth acting on.
- **B107 (hardcoded password)** fires on any default argument named `password`. Here it was a real secret, but the same rule would also flag a harmless placeholder such as `password=""`.
- **R0913 (too many arguments)** on `checkEligibility` is a design opinion, not a defect. It disappeared once I removed the unused `history` argument.

Overall, every finding in this file pointed at something worth changing. A bigger problem than false positives was **false negatives**: the most serious bugs (wrong rate units, a broken eligibility rule, wrong formulas) produced no warnings at all.

### 3. How would you integrate static analysis tools into your actual software development workflow?

- **In the editor:** run Pylint and Flake8 inside VS Code so style and quality issues show up while typing, not after.
- **Pre-commit hook:** use the `pre-commit` framework to run `flake8`, `pylint --fail-under=9.5` and `bandit -ll` (medium severity and above) before every commit, so issues are caught before they reach the repo.
- **CI pipeline:** add a GitHub Actions job that runs all three tools on every push and pull request, saves the reports, and fails the build on any Bandit High/Medium finding or a Pylint score below the agreed threshold.
- **Shared config:** keep the tool settings in `pyproject.toml` / `.flake8` so the whole team uses the same rules. Allow `# nosec` or `# pylint: disable` only with a written reason, reviewed in code review.
- **Not a replacement for tests:** this lab showed the tools miss logic errors, so unit tests (for example, checking `calculate_emi(500000, 0.09, 5) ≈ 10379.18`) are still needed alongside them.

### 4. What tangible improvements did you observe in code quality, readability, or potential robustness after applying the fixes?

- **Measurable:** Pylint went from 5.17 to 10.00/10, Bandit from 8 issues (2 High, 1 Medium) to 0, and Flake8 from 22 to 0.
- **Security:** no plaintext FTP, no hardcoded credentials, no unsafe deserialisation, no predictable IDs and no shelling out to external programs.
- **Correctness:** the demo now prints believable numbers. The EMI is ₹10,379.18, the maximum loan includes interest (₹7.23L instead of ₹9L), interest saved is ₹12,275 instead of ₹62,275, and ineligible applicants are rejected.
- **Robustness:** no crashes on a 0% rate or zero income, files and connections are always closed, the loan book is no longer wiped on each save, and importing the module no longer runs the demo.
- **Readability:** snake_case names, docstrings explaining units (rate as a fraction), named constants (`VALID_LOAN_TYPES`, `MIN_CREDIT_SCORE`) instead of chained comparisons, and flat `if` returns make each function easy to follow and explain.
