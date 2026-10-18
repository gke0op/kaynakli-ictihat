You are an independent reviewer of Turkish case-law citations. You have NOT seen how these were produced.

Input: /home/claude/eval10/hakem_paketi.json. For each case (key) there is:
- `soru`: a Turkish lawyer's request (the client's situation and the legal question),
- `alintilar`: verbatim paragraphs from Yargıtay decisions, each with its citation (`kunye`) and `kimin_sozu`
  (an automatic label saying whose words the paragraph is: YARGITAY = the court's own reasoning;
  ALT MAHKEME = lower-court reasoning recounted in the decision, with "(Yargıtay onadı)" if the Yargıtay upheld it;
  TARAF = a party's pleading; SONUÇ = the operative part; BELİRSİZ = unknown). Read the paragraph yourself;
  the label can be wrong, and if so say so.

Read only that file. Do not search the web, do not open other files.

For each paragraph decide one rating:
- "doğrudan destekliyor": the paragraph itself states a rule or holding that a lawyer could cite for the
  client's position on the question asked, and it is the court's (or an upheld lower court's) reasoning — not a party's claim.
- "ilgili ama aleyhe": directly on point, but against the client's position (useful to know, not support).
- "dolaylı": on the general topic, but does not itself establish the point (procedural, background, different issue).
- "ilgisiz".

Write /home/claude/eval10/hakem_notlari.json:
{"<case>": [{"id": "...", "puan": "<one of the four>", "ses_dogru_mu": true|false, "gerekce": "<one Turkish sentence>"}], ...}

Be strict; you are protecting a lawyer from citing a paragraph that does not say what they need.
Final reply (English, under 150 words): per case, the count of "doğrudan destekliyor", and any label errors.
