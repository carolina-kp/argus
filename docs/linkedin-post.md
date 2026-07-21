# LinkedIn post — MiCA chunking & citation pipeline

Target: ~150-200 words, technical but readable, the kind of post SDX / Sygnum / Taurus
engineers actually engage with. One post, ready to paste.

---

For a regulatory RAG, the failure mode that matters isn't a missed answer. It's a confident
wrong citation. Here's how I designed against it in Argus, my MiCA/FINMA research terminal.

The unlock was chunking. MiCA's official EUR-Lex HTML wraps every article in a
`div.eli-subdivision#art_N`, and there are exactly 149 of them, matching the regulation's
known article count. So the article boundary is a *lossless* chunk boundary: no article
bleeds into its neighbour, and every chunk already carries "Article N" as metadata. Long
articles split at paragraph boundaries, keeping the article ref on each part.

That metadata is what makes citations honest. Retrieval returns article-tagged chunks,
generation must cite them inline, and the response maps each citation back to (document,
article, source URL). Below a calibrated score cutoff, the system refuses instead of
answering.

Then I stopped trusting my own claim and wrote an eval: 18 questions, expected article per
question, measured hit rate. It runs against the live backend. The number is real, imperfect,
and in the README.

How would you handle articles that cross-reference each other? Curious how the Swiss desks
approach this.
