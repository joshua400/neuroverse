# Contributing to NeuroVerse

First off, thank you for considering contributing to NeuroVerse! It's people like you that make NeuroVerse such a great tool.

## Code of Conduct

This project and everyone participating in it is governed by the [NeuroVerse Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs
- Use a clear and descriptive title.
- Describe the exact steps which reproduce the problem.
- Explain which behavior you expected to see instead and why.

### Suggesting Enhancements
- Check if there's already a similar suggestion.
- Explain why this enhancement would be useful to most NeuroVerse users.

### Pull Requests
1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes (`npm test` or `pytest`).
5. Make sure your code lints.

## Styleguides

### Git Commit Messages
- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less

### TypeScript Styleguide
- Use functional programming patterns where possible.
- Ensure all new tools are registered in `src/index.ts`.
- Use Zod for all input validation.
