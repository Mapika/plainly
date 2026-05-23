# Where the tells come from

The lexical and structural tells in this directory are sourced, not guessed. They fall
into three evidence grades. Weights are deliberately low and clustering-based — no single
tell is decisive — because tells decay as models change (see "Decay" below).

## Grade 1 — measured in peer-reviewed / large-corpus studies (AI vocabulary)

These words were measured as statistically over-represented in post-ChatGPT text against a
counterfactual baseline. They are general-register (flagged in any genre).

- **Kobak, D., González-Márquez, R., Horvát, E.-Á., & Lause, J. (2024/2025).** "Delving into
  LLM-assisted writing in biomedical publications through excess vocabulary." arXiv:2406.07016.
  14M PubMed abstracts; excess-frequency ratio *r* and gap *δ* vs. a 2021–2022 baseline.
  Source of: delve, underscore, intricate, showcasing, meticulous, pivotal, realm, boasts.
- **Liang, W., et al. (2024).** "Monitoring AI-Modified Content at Scale: ... ChatGPT on AI
  Conference Peer Reviews." ICML 2024. arXiv:2403.07183. Per-word fold-increase in AI vs.
  human reviews. Source of: meticulous (34.7×), commendable (9.8×), intricate (11.2×),
  plus the adjective/adverb lists (versatile, noteworthy, invaluable, poised, …).
- **Kousha, K., & Thelwall, M. (2025).** "How much are LLMs changing the language of academic
  papers after ChatGPT?" arXiv:2509.09596. 6 databases + 2.4M PMC full texts. delve +1,500%,
  underscore +1,000%, intricate +700%; co-occurrence of underscore↔pivotal↔delve. Source of
  the second wave: heighten, nuance, bolster, foster, interplay, garner.

**Deliberately excluded** (measured but too common → false positives): significant, crucial,
comprehensive, enhance, potential, additionally, notably, particularly. Geng & Trotta show
these keep rising precisely because they are too ordinary to look suspicious.

## Grade 2 — measured frequency counts / ranked lists (marketing buzzwords)

`register: marketing` — damped outside the marketing genre (see `scan.GENRE_MULT`).

- **Sherk, A.** "The Most Overused Buzzwords and Marketing Speak in Press Releases" (PRWeb
  corpus, ~3.8M releases). https://www.adamsherk.com/public-relations/most-overused-press-release-buzzwords/
  Source of: state-of-the-art, world-class, award-winning, "leading"/"best"-class puffery.
- **LinkedIn annual buzzword lists (2010–2018)** and the LinkedIn "Marketing Madness" bracket
  (winner: *disruption*; seeds: synergy, low-hanging fruit, utilize, actionable). Survey-ranked.
- **Mediaocean (2022) / TrustRadius (2024)** most-annoying-buzzword surveys: future-proof, AI,
  transparency. Source of: synergy, disrupt, low-hanging fruit, future-proof, move the needle,
  double down.

## Grade 3 — editorial consensus, no published frequency count (announcement / puffery)

Condemned by every style authority but never formally counted. They are legitimate *quality*
smells regardless of authorship, which is why plainly flags them (we sell quality, not a
verdict).

- **Wikipedia, "Signs of AI writing."** https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing
  Source of the puffery-significance phrases ("plays a pivotal role", "rich tapestry",
  "nestled in the heart of", "leaves an indelible mark") and the emoji-as-formatting tell.
- **Orwell, "Politics and the English Language" (1946):** "Never use a metaphor, simile or
  figure of speech you are used to seeing in print." The grounding principle for the
  announcement-cliché pattern ("thrilled to announce", "the best is yet to come", …).

## Emoji (`emoji-measured`, `emoji-hype`, `emoji-bullet`)

- **Merrill, J. & Schaul, K.** "What are the clues that ChatGPT wrote something? We analyzed
  its style." *The Washington Post*, Nov 2025. 328,744 gpt-4o messages. **Measured tells:**
  ✅ (~11× human rate, ~⅓ of messages), 🧠 (~10×), 🔹 (~10×) → `emoji-measured`.
- **Buffer, "Most Popular Emojis in Social Posts 2025."** Shows 🚀✨🔥💡🎉 are also the *top
  human* social emoji → high false-positive risk. So they live in `emoji-hype` at low weight,
  `register: marketing` (damped in docs/prose), never decisive alone.
- Emoji-as-bullet (`emoji-bullet`) is the structural pattern the WaPo data and Wikipedia both
  point to — a formatting tell independent of which glyph.

## Decay (why weights are low and dated)

- **Geng, M. & Trotta, R. (2025).** "Human-LLM Coevolution: Evidence from Academic Writing."
  arXiv:2502.09606. delve/showcasing/intricate/realm/pivotal began **declining ~April 2024**
  once publicized. Marked `tier: stale` here. Re-run the eval periodically; tells are
  non-stationary.
