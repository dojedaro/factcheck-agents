# Passkeys vs. SMS One-Time Passwords for Consumer Banking Login: Security and Usability Trade-offs

> What are the main security and usability trade-offs between passkeys and SMS one-time passwords for consumer banking login?

The evidence favors passkeys over SMS OTP on both security and usability, but much of the usability data comes from non-bank services and vendor sources. On security, NIST SP 800-63B-4 names SMS/voice (PSTN) out-of-band authentication as its only 'restricted' authenticator because of added false-acceptance risk [F1][F2]. A secondary summary says SMS codes remain allowed at AAL2 with conditions but not at AAL3 [F4], reportedly because OTP is not phishing-resistant [F5]. On usability, FIDO Alliance data reports passkey sign-ins as faster and more often successful than methods that include SMS codes [F7][F8], though the size of the success gap differs between reports [F8][F9]. Bank evidence suggests adoption depends heavily on deployment: one bank reports 42% passkey use for transaction approval [F11], while a vendor says opt-in-only rollouts stay below 1% [F12].

## Bottom line

The available evidence suggests passkeys are the stronger choice for consumer banking login. SMS OTP carries a formal regulatory caveat under NIST [F1][F2] and cannot reach the highest assurance level [F4][F5]. Reported passkey sign-ins are faster and succeed more often [F7][F8][F9][F10]. The main practical trade-off is adoption: the benefits depend on whether users actually enroll, which appears to hinge on how prominently banks present passkeys [F11][F12]. SMS OTP's chief advantage, staying allowed with conditions at AAL2 [F4], is a compliance floor rather than a security strength.

## Security and regulatory standing

NIST SP 800-63B-4 names exactly one restricted authenticator: using the PSTN (SMS/voice) for out-of-band authentication [F1]. NIST defines a restricted authenticator as one with additional risk of false acceptance, which makes it subject to additional requirements [F2]. NIST indicates it may revisit this restricted status as the threat landscape evolves [F3]. That evidence is only partial, so it should not be read as a commitment to tighten or loosen the status.

According to a secondary vendor summary of the final July 2025 SP 800-63B-4, SMS/voice codes are still allowed at AAL2 if the provider offers an alternative and explains the risk, but not at AAL3 [F4]. Another secondary summary attributes the AAL3 ceiling to OTP not being verifier-impersonation-resistant, meaning not phishing-resistant [F5]. The evidence provided does not directly state passkeys' own NIST assurance level, so this report can only say that SMS OTP is capped, not that passkeys are certified at AAL3.

## Usability: speed and sign-in success

The FIDO Alliance Passkey Index (2025) reports that passkey sign-ins averaged 8.5 seconds. That is 73% faster than other methods, including email verification, SMS codes and social login, which averaged 31.2 seconds [F7]. The same index reports a 93% success rate for passkeys versus 63% for other methods [F8]. These comparisons group SMS with other methods rather than isolating it, and are rated only partially supported.

The success gap is contested. A secondary report on a 2026 Passkey Index covering 15 consumer services gives 93% for passkeys versus 78% for passwords and traditional MFA such as SMS OTP. It also says passkeys are 2.8 times faster [F9]. That 78% figure conflicts with the 63% in the 2025 index [F8]. The same report says passkeys carry 36% of successful sign-ins, a share that excludes account recovery [F9].

The most direct head-to-head comparison comes from Mercari, an e-commerce company rather than a bank. There, passkeys reportedly succeeded 82.5% of the time versus 67.7% for SMS OTP [F10]. Across sources, passkeys appear to succeed more often than SMS-based login, but the reported size of the advantage ranges from roughly 15 to 30 percentage points [F8][F9][F10].

## Operational cost and delivery reliability of SMS

SMS OTP has delivery and cost drawbacks that passkeys avoid. Mercari reportedly faced global messaging fees and complaints about delayed or missing codes while using SMS OTP [F10]. A vendor, Authsignal, says banks pay $0.01–$0.10 per SMS OTP depending on region and that 10–15% of SMS OTPs never reach users [F13]. These figures come from a vendor source with partial support, so treat them as indicative rather than established.

## Adoption in banking depends on deployment

Passkey benefits only materialize if customers enroll. In one bank case study, 42% of ABANCA's mobile banking users now approve transactions with passkeys [F11]. Note that this concerns transaction authorization, which is related to but not identical to login.

By contrast, a vendor (Corbado) reports that when banks offer passkeys only as an opt-in setting, adoption stays below 1%. In that case SMS OTP costs remain [F12]. This claim is only partially supported. If it holds, deployment design determines whether a bank realizes passkeys' usability and cost advantages; simply offering the feature is not enough.

## Limitations

- None of the named participants in the FIDO 2025 Passkey Index were banks (the data came from services such as Amazon, Google, Microsoft and PayPal), and the Mercari comparison is e-commerce. Usability figures may not transfer directly to banking login [F8][F10].
- The 'other methods' baselines in the FIDO data bundle SMS codes with email verification, social login and passwords, so they are not clean SMS-vs-passkey comparisons [F7][F9].
- Reported baseline success rates conflict: 63% in the 2025 index [F8] versus 78% in a secondary report on the 2026 index [F9].
- Several key figures (SMS cost, non-delivery rate, opt-in adoption, NIST AAL interpretation) come from vendor or secondary summaries, and several are rated only partially supported [F4][F5][F12][F13].
- The evidence does not cover specific attack vectors against SMS (e.g., SIM swapping or interception), passkey account recovery and device-loss scenarios, accessibility, or users without compatible devices. These are important trade-offs that cannot be assessed here.
- The evidence does not directly state the NIST assurance level passkeys achieve; it only establishes that SMS OTP is restricted and capped below AAL3 [F1][F4][F5].
- The ABANCA figure concerns transaction authorization rather than login, and no bank-specific success-rate or speed data were provided [F11].

## References

- **[F1]** [NIST Special Publication 800-63B](https://pages.nist.gov/800-63-4/sp800-63b.html): "there is one restricted authenticator: the use of the PSTN for out-of-band authentication"
- **[F2]** [NIST Special Publication 800-63B](https://pages.nist.gov/800-63-4/sp800-63b.html): "has additional risk of false acceptance associated with its use and is therefore subject to additional requirements"
- **[F3]** [NIST Special Publication 800-63B](https://pages.nist.gov/800-63-4/sp800-63b.html) *(partially supported)*: "NIST may adjust the restricted status of out-of-band authentication using the PSTN based on the evolution of the threat landscape"
- **[F4]** [Is SMS OTP Still Allowed? NIST, PSD2, PCI DSS (2026)](https://www.broadnet.me/blog/sms-otp-security-standards-2026): "still allowed at AAL2 if the provider offers an alternative and explains the risk, but not at AAL3"
- **[F5]** [OTP Security & NIST 800-63B: 2026 Rate-Limiting Guide](https://identitychallengecard.avatier.com/en/blog/otp-nist-800-63b-defense-2026): "OTP never reaches AAL3 because it is not verifier-impersonation-resistant"
- **[F7]** [FIDO Alliance Launches Passkey Index, Revealing Significant Passkey Uptake and Business Benefits](https://fidoalliance.org/fido-alliance-launches-passkey-index-revealing-significant-passkey-uptake-and-business-benefits/) *(partially supported)*: "Traditional approaches including email verification, SMS codes, and social login options took an average of 31.2 seconds."
- **[F8]** [FIDO Alliance Launches Passkey Index, Revealing Significant Passkey Uptake and Business Benefits](https://fidoalliance.org/fido-alliance-launches-passkey-index-revealing-significant-passkey-uptake-and-business-benefits/) *(partially supported)*: "Passkey sign-ins have a 93% success rate, compared to 63% for other methods"
- **[F9]** [FIDO Passkey Index 2026: passkeys now carry 36% of sign-ins](https://startwithidentity.com/blog/2026-10-15-fido-passkey-index-2026-passkeys-reach-36-percent-of-sign-ins/) *(partially supported)*: "Passkey sign-ins succeeded 93% of the time versus 78% for passwords and traditional MFA such as SMS OTP"
- **[F10]** [Passkeys vs. Passwordless vs. Phishing-Resistant MFA](https://www.corbado.com/blog/passkeys-passwordless-phishing-resistant-mfa) *(partially supported)*: "The passkey adoption achieved an 82.5% success rate for sign-ins compared to 67.7% for SMS OTP."
- **[F11]** [Passkey Adoption Statistics 2026](https://state-of-passkeys.io/case-studies): "42% of ABANCA's mobile banking users now authorize transactions using passkeys"
- **[F12]** [10 Passkey Deployment Mistakes Banks make](https://www.corbado.com/blog/passkey-deployment-mistakes-banks) *(partially supported)*: "Adoption stagnates at <1% as users fail to discover or understand the feature."
- **[F13]** [June 2025 SMS OTP regulatory updates: Banking's global shift to secure authentication](https://www.authsignal.com/blog/articles/june-2025-sms-otp-regulatory-updates-bankings-global-shift-to-secure-authentication) *(partially supported)*: "studies show that 10-15% of SMS OTPs never reach users due to network congestion, carrier filtering, or device issues"

---
*2 sub-questions, 1 research round(s), 12/13 findings passed checks, 12 cited. Cost $0.95, 97s.*
