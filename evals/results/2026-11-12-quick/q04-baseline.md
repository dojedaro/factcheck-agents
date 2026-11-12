# EU AI Act: what providers of general-purpose AI models must do, and when

> What obligations does the EU AI Act place on providers of general-purpose AI models, and when do they apply?

Every provider of a general-purpose AI (GPAI) model has to meet four core duties: keep technical documentation, give information to downstream providers, have a copyright policy, and publish a summary of training content. Providers based outside the EU must also appoint a representative in the EU [F1][F3][F4][F5][F6]. Models trained with more than 10^25 FLOPs are presumed to pose 'systemic risk'. Their providers must notify the Commission and also carry out evaluations, mitigate risks, report incidents and ensure cybersecurity [F9][F10][F11]. These obligations started to apply on 2 August 2025, but the Commission can only enforce them, including with fines, from 2 August 2026 [F15][F17]. Models already on the market before 2 August 2025 have until 2 August 2027 to comply [F18].

## Obligations for all GPAI model providers (Article 53)

Every GPAI provider must do the following:

- **Technical documentation:** prepare and keep it up to date, and supply it to the AI Office on request [F1]. It must cover the training and testing process and the evaluation results [F2].
- **Information for downstream providers:** give companies that build the model into their own AI systems enough information to understand its capabilities and limitations [F3].
- **Copyright:** have a policy for complying with EU copyright law [F4].
- **Training data summary:** publish a sufficiently detailed summary of the content used to train the model [F5].
- **EU representative:** providers based outside the EU must appoint an authorised representative in the EU before placing the model on the market [F6].

The Commission's guidelines presume that a model trained with more than 10^23 FLOPs is a GPAI model [F13]. A company that modifies someone else's model may itself count as a provider if the modification uses more than one-third of the original model's training compute [F14].

## Open-source exemption

Some of these obligations do not apply to models released under a free and open-source licence with public weights and parameters [F7]. The exemption does not cover models with systemic risk [F8].

## Extra obligations for models with systemic risk (Articles 51, 52 and 55)

A model is presumed to pose systemic risk when its cumulative training compute exceeds 10^25 FLOPs [F9]. A model below that threshold can still be designated as systemic-risk because of its reach or capabilities [F12].

Providers must notify the Commission without delay, and in any case within two weeks, once their model meets the criterion [F10].

On top of the Article 53 duties, these providers must:
- evaluate the model
- assess and mitigate systemic risks
- track and report serious incidents
- ensure adequate cybersecurity [F11]

## Timeline

| Date | What happens |
|---|---|
| 10 July 2025 | The voluntary Code of Practice is published [F21] |
| 2 August 2025 | Obligations start to apply to models placed on the market from this date [F15] |
| 2 August 2025 – 2 August 2026 | The AI Office offers close collaboration, especially with Code signatories [F16] |
| 2 August 2026 | The Commission begins enforcing full compliance, including fines [F17] |
| 2 August 2027 | Deadline for models placed on the market before 2 August 2025 [F18] |

## How providers can show compliance

Until a harmonised standard is published, providers may rely on codes of practice under Article 56 to show they comply [F19]. Providers that follow neither an approved code nor a harmonised standard must show other adequate means of compliance, which the Commission assesses [F20]. Following the Code is voluntary, and the Code says that adhering to it is not conclusive evidence of compliance [F22].

## Limitations

- The maximum fine amounts for GPAI providers (Article 101) were not found in the retrieved sources, so they are not stated here.
- Several findings come from secondary sources such as law-firm summaries and unofficial copies of the Act, not from the Official Journal text on EUR-Lex. The full text of Article 55 was not retrieved directly.
- Proposals to amend the AI Act's timelines (for example a 'digital omnibus') were not checked. Dates may change after these sources were published.
- The compute thresholds are presumptions that can be rebutted or overridden by designation, and the Commission can update them. The 10^23 FLOP threshold for what counts as a GPAI model comes from non-binding guidelines.
- The content of the training-data summary template and the detailed chapters of the Code of Practice were not examined.

## References

- **[F1]** [What legal obligations do providers of general-purpose AI models face under the AI Act as of 2 August 2025?](https://ai-act-service-desk.ec.europa.eu/en/ai-act/faq/what-legal-obligations-do-providers-general-purpose-ai-models-face-under-ai-act-2-august): "draw up and maintain technical documentation about the model, including information about the development process, to provide to the AI Office upon request"
- **[F2]** [Art. 53 AI Act - Obligations for providers of general-purpose AI models - AI Act](https://ai-act-law.eu/article/53/): "including its training and testing process and the results of its evaluation"
- **[F3]** [What legal obligations do providers of general-purpose AI models face under the AI Act as of 2 August 2025?](https://ai-act-service-desk.ec.europa.eu/en/ai-act/faq/what-legal-obligations-do-providers-general-purpose-ai-models-face-under-ai-act-2-august): "provide information and documentation to downstream AI system providers to help them understand the model's capabilities and limitations"
- **[F4]** [What legal obligations do providers of general-purpose AI models face under the AI Act as of 2 August 2025?](https://ai-act-service-desk.ec.europa.eu/en/ai-act/faq/what-legal-obligations-do-providers-general-purpose-ai-models-face-under-ai-act-2-august): "implement a policy to comply with Union copyright law and related rights"
- **[F5]** [EU AI Act Article 53: Obligations for Providers of General-Purpose AI Models](https://www.euaiact.com/article/53): "draw up and make publicly available a sufficiently detailed summary about the content used for training of the general-purpose AI model"
- **[F6]** [What legal obligations do providers of general-purpose AI models face under the AI Act as of 2 August 2025?](https://ai-act-service-desk.ec.europa.eu/en/ai-act/faq/what-legal-obligations-do-providers-general-purpose-ai-models-face-under-ai-act-2-august): "if they are established outside the EU, appoint an authorised representative in the Union before placing their model on the market"
- **[F7]** [The second wave of AI Act provisions enters into force](https://www.loyensloeff.com/insights/news--events/news/the-second-wave-of-ai-act-provisions-enters-into-force/): "Some of the obligations listed above do not apply if the model is released under a free and open-source license"
- **[F8]** [Art. 53 AI Act - Obligations for providers of general-purpose AI models - AI Act](https://ai-act-law.eu/article/53/): "This exception shall not apply to general-purpose AI models with systemic risks."
- **[F9]** [High-level summary of the AI Act](https://artificialintelligenceact.eu/high-level-summary/): "GPAI models present systemic risks when the cumulative amount of compute used for its training is greater than 10^25"
- **[F10]** [High-level summary of the AI Act](https://artificialintelligenceact.eu/high-level-summary/): "Providers must notify the Commission if their model meets this criterion without delay and in any case within 2 weeks."
- **[F11]** [High-level summary of the AI Act](https://artificialintelligenceact.eu/high-level-summary/): "must also conduct model evaluations and risk assessments and mitigations, track and report serious incidents and ensure cybersecurity protections"
- **[F12]** [EU AI Act GPAI Rules: What Providers Need to Know](https://www.jaggaer.com/blog/eu-ai-act-rules-for-general-purpose-ai): "The Scientific Panel may also designate models below 10^25 FLOPs based on reach or capability."
- **[F13]** [European Commission Issues Guidelines for Providers of General-Purpose AI Models](https://www.wilmerhale.com/en/insights/blogs/wilmerhale-privacy-and-cybersecurity-law/20250724-european-commission-issues-guidelines-for-providers-of-general-purpose-ai-models): "The guidelines stipulate that models exceeding 10^23 FLOPs are presumptively considered GPAI models within the meaning of the AI Act."
- **[F14]** [European Commission Issues Guidelines for Providers of General-Purpose AI Models](https://www.wilmerhale.com/en/insights/blogs/wilmerhale-privacy-and-cybersecurity-law/20250724-european-commission-issues-guidelines-for-providers-of-general-purpose-ai-models): "the training compute used for the modification is greater than one-third of the training compute of the original model"
- **[F15]** [Guidelines on obligations for General-Purpose AI providers](https://digital-strategy.ec.europa.eu/en/faqs/guidelines-obligations-general-purpose-ai-providers): "The AI Act obligations for providers of general-purpose AI models enter into application on 2 August 2025."
- **[F16]** [Guidelines on obligations for General-Purpose AI providers](https://digital-strategy.ec.europa.eu/en/faqs/guidelines-obligations-general-purpose-ai-providers): "the AI Office will offer to collaborate closely in particular with providers who adhere to the Code of Practice"
- **[F17]** [Guidelines on obligations for General-Purpose AI providers](https://digital-strategy.ec.europa.eu/en/faqs/guidelines-obligations-general-purpose-ai-providers): "from 2 August 2026 onwards, the Commission will enforce full compliance with all obligations for providers of general-purpose AI models, including through fines."
- **[F18]** [Guidelines on obligations for General-Purpose AI providers](https://digital-strategy.ec.europa.eu/en/faqs/guidelines-obligations-general-purpose-ai-providers): "Providers of general-purpose AI models placed on the market before 2 August 2025 must comply with the AI Act obligations by 2 August 2027."
- **[F19]** [Art. 53 AI Act - Obligations for providers of general-purpose AI models - AI Act](https://ai-act-law.eu/article/53/): "Providers of general-purpose AI models may rely on codes of practice within the meaning of Article 56 to demonstrate compliance"
- **[F20]** [Art. 53 AI Act - Obligations for providers of general-purpose AI models - AI Act](https://ai-act-law.eu/article/53/): "shall demonstrate alternative adequate means of compliance for assessment by the Commission."
- **[F21]** [The General-Purpose AI Code of Practice](https://digital-strategy.ec.europa.eu/en/policies/contents-code-gpai): "The code was published on July 10, 2025."
- **[F22]** [Code of Practice for General-Purpose AI Models Published: Compliance Just Got Clearer (Participation Still Optional)](https://www.crowell.com/en/insights/client-alerts/code-of-practice-for-general-purpose-ai-models-published-compliance-just-got-clearer-participation-still-optional): "adherence to the Code does not constitute conclusive evidence of compliance with these obligations under the AI Act"

---
*1 sub-questions, 1 research round(s), 22/22 findings passed checks, 22 cited. Cost $0.55, 79s.*
