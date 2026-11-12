# Passkeys vs SMS OTP for Consumer Banking Login: Security and Usability Trade-offs

> What are the main security and usability trade-offs between passkeys and SMS one-time passwords for consumer banking login?

Passkeys are phishing-resistant because they use public-key cryptography. SMS OTPs are human-readable codes that can be phished, relayed in real time, SIM-swapped or intercepted [F1][F3][F5]. Published industry data also suggests passkeys are faster and fail less often at login [F9][F10][F11]. SMS OTP still has the edge on universal reach and needs no setup [F2]. Passkeys' main weaknesses are account recovery, dependence on the Apple/Google ecosystem, abuse of enrollment, and low consumer adoption in banking so far [F12][F13][F14][F15]. In practice, the security gain from passkeys largely disappears if SMS OTP is kept as the fallback or recovery channel [F4][F13].

## Security: phishing and channel attacks

An SMS OTP is a code the user reads and types. A fake site can capture it, a phishing kit can relay it in real time, and malware that reads messages can steal it [F1][F3]. The bank does not control the carrier delivery path, so codes can also be taken through SIM swap, port-out fraud or SS7 interception [F5]. A SIM swap works by tricking the mobile operator into moving the victim's number to a SIM the attacker controls, after which the attacker receives the codes [F6]. The scale is growing: UK SIM-swap fraud rose by more than 1,000% in 2024 [F7], and US losses reported to the FBI passed $72 million in 2022 [F8]. Regulators in more than 25 markets are moving banks away from SMS OTP [F5]. Passkeys avoid these attacks because there is no shared code the user can hand over [F1][F3].

## Where passkeys move the risk

Passkeys do not remove risk; they shift it. Exposure moves toward device compromise, enrollment abuse and recovery abuse, and session theft and endpoint malware remain [F16]. One serious gap is unsecured enrollment: an attacker with a harvested password may register their own passkey and lock the real customer out [F14]. Passkeys also prove who is logging in, not whether a given payment or new payee was really intended, so transaction-level controls are still needed [F17]. Finally, if SMS stays as the fallback, the account is only as strong as SMS [F4][F13].

## Usability and cost

FIDO Alliance data shows a 93% sign-in success rate for passkeys, compared with 63% for a mix of other methods that includes OTPs [F9]. One vendor's direct comparison found passkey sign-ins averaged 14 seconds versus 23 seconds for SMS OTP, with first-try success of 100% versus 94% [F10]. Organizations that deployed passkeys reported 81% fewer login-related help desk incidents [F11]. Passkeys also avoid the per-message carrier fees SMS incurs [F1]. SMS OTP's real usability strength is reach: any phone can receive a text with no setup [F2]. Banks adopting passkeys must still provide another way in for customers whose devices don't support them [F19].

## Recovery, lock-in and adoption

Because a passkey is tied to a device, losing that device creates friction for the genuine customer [F13]. Synced passkeys reduce this risk, but only as far as the user's other devices hold the key; device-bound passkeys offer no easy recovery [F18]. Synced banking passkeys also depend on Apple or Google, so losing access to an Apple ID can mean losing the passkeys [F14]. In a USENIX study, experts named recovery and fallback, friction, and regulatory requirements such as PSD2 as the biggest barriers to deployment [F15]. Consumer passkey adoption in financial services remains in single digits [F12]. Recovery that falls back to weak checks brings back the vulnerabilities passkeys were meant to remove [F19]. Commentators therefore recommend stronger re-verification for recovery, such as eID, ID documents with liveness checks, or in-branch checks [F13].

## Bottom line

For banking login, passkeys are much stronger against phishing and SIM-swap account takeover, and the available data points to smoother logins [F1][F9][F10]. SMS OTP offers universal, setup-free reach and a familiar experience [F2]. The deciding factor is how banks handle enrollment, recovery and fallback. If SMS remains the escape hatch, much of the passkey security benefit is lost [F4][F13][F14].

## Limitations

- Much of the evidence comes from authentication vendors and industry blogs (Corbado, Authsignal, MojoAuth, NHIMG), which have commercial interests in passkeys. Independent peer-reviewed comparisons of passkeys and SMS OTP specifically in banking are scarce.
- The 93% vs 63% FIDO figure compares passkeys with a mix of 'other methods' (social login, MFA, OTPs), not with SMS OTP alone. The only direct passkey-vs-SMS timing figures come from a single vendor's data [F10].
- Several sources carry 2026 dates and report figures (for example, adoption counts) that I could not check against primary FIDO or regulator documents.
- Usability for older, low-income or feature-phone users, and accessibility generally, are not well covered by the quantitative data. SMS's universal-reach advantage [F2] may matter more for those groups.
- I did not retrieve primary regulatory texts (NIST SP 800-63, PSD2 RTS, UAE/MAS circulars). The regulatory claims rest on secondary summaries.

## References

- **[F1]** [Passkeys vs SMS OTP: Conversion, Cost & Security](https://www.corbado.com/blog/passkeys-vs-sms-otp): "An SMS OTP is a human-readable code, which makes it vulnerable to phishing, SIM-swap attacks and malware that reads incoming messages."
- **[F2]** [Passkeys vs SMS OTP: Conversion, Cost & Security](https://www.corbado.com/blog/passkeys-vs-sms-otp): "SMS OTP keeps one real advantage: near-universal reach, since every phone can receive a text without setup."
- **[F3]** [What is the difference between SMS OTP and phishing-resistant passkeys for authentication security?](https://nhimg.org/faq/what-is-the-difference-between-sms-otp-and-phishing-resistant-passkeys-for-authe/): "SMS OTP can be defeated by relaying or coercing the code in real time."
- **[F4]** [What is the difference between SMS OTP and phishing-resistant passkeys for authentication security?](https://nhimg.org/faq/what-is-the-difference-between-sms-otp-and-phishing-resistant-passkeys-for-authe/): "If a platform supports passkeys but still lets users fall back to SMS for high-risk transactions, the security benefit is only partial."
- **[F5]** [SMS OTP bans are forcing a reset in banking authentication](https://nhimg.org/articles/sms-otp-bans-are-forcing-a-reset-in-banking-authentication): "the bank does not control the delivery path, so the code can be copied, redirected, or harvested through SIM swap"
- **[F6]** [Fraudulent subscriber identity module (SIM) swap detection](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/10178223): "the operator of the mobile telephone network is tricked into deactivating the victim's legitimate SIM card"
- **[F7]** [SIM-swap fraud: Scam prevention guide](https://specopssoft.com/blog/sim-swap-fraud-prevention-guide-2025/): "According to the National Fraud Database, SIM-swap fraud jumped by over 1,000% in 2024."
- **[F8]** [What Are OTPs in Messages? SMS One-Time Passwords, Risks, and Safer Alternatives](https://mojoauth.com/blog/what-are-otps-in-messages-sms-risks): "SIM-swap fraud losses reported to the FBI Internet Crime Complaint Center climbed past $72 million in 2022 alone"
- **[F9]** [FIDO Passkey Index October 2026: What the Numbers Mean for Your Roadmap](https://mojoauth.com/blog/fido-passkey-index-october-2026-what-it-means): "2025 compared against “other methods” including social login, MFA and OTPs (63%)."
- **[F10]** [SMS-based authentication: Why it’s no longer enough for security](https://www.authsignal.com/blog/articles/why-sms-based-authentication-is-no-longer-enough-for-secure-account-protection): "Average sign-in time drops to 14 seconds versus 23 seconds for SMS OTP, and first-try success rates hit 100% compared to 94% for SMS."
- **[F11]** [FIDO Passkeys: Passwordless Authentication](https://fidoalliance.org/passkeys/): "81%  Reduction in login-related help desk incidents – Source: FIDO Alliance Passkey Index"
- **[F12]** [10 UX Patterns That Drive 80%+ Passkey Adoption (With Real Examples)](https://mojoauth.com/blog/passkey-ux-patterns-drive-adoption): "consumer passkey adoption in financial services stays in single digits"
- **[F13]** [The end of trust at login: Why banking’s new front line is inside the session - qorusglobal.com](https://www.qorusglobal.com/content/31819-the-end-of-trust-at-login-why-bankings-new-front-line-is-inside-the-session): "Because a passkey is cryptographically bound to a physical device, losing the device creates friction for the legitimate user."
- **[F14]** [10 Passkey Deployment Mistakes Banks make](https://www.corbado.com/blog/passkey-deployment-mistakes-banks): "If a user gets locked out of their Apple ID, they lose their passkeys."
- **[F15]** [Why Aren't We Using Passkeys? Obstacles Companies ...](https://www.usenix.org/system/files/sec24summer-prepub-618-lassak.pdf): "key barriers to adoption, including account recovery, friction,"
- **[F16]** [How should banks evaluate passkeys as a replacement for passwords in customer authentication programs?](https://nhimg.org/faq/how-should-banks-evaluate-passkeys-as-a-replacement-for-passwords-in-customer-au/): "banks can shift some risk from secret theft to device compromise, enrollment abuse, and recovery abuse."
- **[F17]** [Authentication does not equal authorization: Are we asking passkeys to prove too much?](https://www.techradar.com/pro/authentication-does-not-equal-authorization-are-we-asking-passkeys-to-prove-too-much): "Passkeys are useful, but they were never designed to answer all of these questions on their own."
- **[F18]** [Device-Bound vs. Synced Credentials: A Comparative Evaluation of Passkey Authentication](https://arxiv.org/pdf/2501.07380): "Thus, device-bound passkeys do not provide Easy-Recovery-from-Loss."
- **[F19]** [Banks replace passwords with passkeys to strengthen digital access](https://bankquality.com/blog/banks-replace-passwords-with-passkeys-to-strengthen-digital-access): "Recovery flows that revert to weak identity checks risk reintroducing the same vulnerabilities that passkeys are meant to remove."

---
*1 sub-questions, 1 research round(s), 19/19 findings passed checks, 19 cited. Cost $0.51, 78s.*
