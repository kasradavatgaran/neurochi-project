# Final changes — implementation checklist

This checklist follows the requested order: UI, model/performance, then RAG.

- [x] 1. Verify the PDF issues and preserve the supplied landing design.
- [x] 2. Make the landing the home page and connect its sign-in controls.
- [x] 3. Preserve a visitor's question through registration, then create a general chat and generate the answer reliably.
- [x] 4. Require a first child after creating the parent profile; preserve existing general chats.
- [x] 5. Add the child's test history, result dialog and completed game cards; fix sidebar layout.
- [x] 6. Fix test navigation and game selection; report uncovered age ranges without inventing clinical content.
- [x] 7. Verify the requested Flash model on Liara and measure each stage of a response.
- [x] 8. Optimize SQLite access, transaction lifetime and non-chat API latency using measured evidence.
- [x] 9. Evaluate RAG source coverage, titles, translations and relevance; compare title retrieval and smaller context before changing defaults.
- [x] 10. Build and verify the UI/API flows; document measurements, resolved issues and remaining external limitations.

## Acceptance notes

- The landing keeps the supplied HTML appearance. A guest question is retained without generating an anonymous answer.
- Generation starts only after registration and first-child onboarding finish, in a new general chat.
- Loading, refresh and retry must not silently discard the question or create duplicate conversations.
- RAG documents are evidence, not instructions. Unused or unrelated documents must not become citations.
- Timing separates SQLite, context preparation, query rewriting, retrieval/embedding and model first-token/total time.
- Only confirmed translation defects are retranslated; no automatic scrape is performed.

Results and limitations: [final_changes_report.md](final_changes_report.md).
