# Contributing

Thank you for your interest. This is an early research prototype, so small, focused contributions are the easiest to review.

1. Open an issue describing the bug, question, or idea.
2. Fork the repository and create a branch.
3. Run the quick tests from the `src/` directory:
   ```bash
   python exhaustive_tests.py quick
   python maintain_tests.py quick
   python hypergraph_check.py
   ```
4. Open a pull request that explains what changed and why.

Good first contributions: additional tests, new certificate or label types (for example interval or prefix labels), clearer documentation, and ports of the checker to Lean 4 or Dafny.
