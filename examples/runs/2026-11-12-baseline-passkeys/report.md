# Passkeys vs SMS OTP for Consumer Banking Login: Security and Usability Trade-offs

> What are the main security and usability trade-offs between passkeys and SMS one-time passwords for consumer banking login?

On security, passkeys clearly beat SMS OTP. Passkeys are phishing-resistant [F21]. SMS codes are human-readable and can be phished, SIM-swapped, relayed in real time or read by malware [F2][F5][F8]. The main reasons to keep SMS are that it works on almost any phone without setup [F1] and that people already know how to use it. On usability, the sources mostly favour passkeys: vendor and FIDO data show faster sign-ins and higher success rates [F10][F11][F12], and passkeys avoid per-message SMS fees [F3]. The hardest trade-off is account recovery and fallback. Passkey recovery can be complex [F16][F14], and if a bank falls back to SMS for recovery or high-risk actions, much of the security gain is lost [F9][F13].

## Security: phishing resistance vs a shared, interceptable code

SMS OTP is a code the user can read and type, so it can be phished, captured through SIM swaps or read by malware on the phone [F2]. The bank does not control the delivery path. That leaves codes open to SIM swap, port-out fraud, SS7 interception and phishing [F5]. Attackers can also defeat SMS OTP by relaying the code, or coercing the user into revealing it, in real time [F8]. Smishing pages, for example, capture both the password and the OTP as the victim types them [F20]. SIM-swap scams also often involve fraudsters asking victims to read out their OTP [F22]. Once a number is hijacked, the bank's OTPs go straight to the criminal [F7], and SIM-swap losses reported to the FBI passed $72 million in 2022 [F6]. Passkeys, by contrast, are described as always strong and phishing-resistant [F21]. In a mapping to NIST SP 800-63, they align with high-assurance authenticators, while SMS maps to lower-assurance MFA [F19]. Regulators in more than 25 markets are reported to be moving banks away from SMS OTP [F4].

## Usability: speed, success rates and reach

Vendor and industry data report that passkeys are faster and more reliable. One provider reports average sign-in times of 14 seconds with passkeys versus 23 seconds with SMS OTP, and first-try success of 100% versus 94% [F10]. The FIDO Passkey Index 2026 reports 93% sign-in success for passkeys versus 78% for passwords and traditional MFA [F11]. Other FIDO figures show passkey sign-ins averaging 8.5 seconds versus 31.2 seconds for passwords [F12]. Passkeys also remove the need to wait for and type a code, and they avoid per-message carrier fees [F3]. SMS OTP's big usability advantage is reach: every phone can receive a text without any setup [F1]. Passkeys do not work on some older or less capable devices [F15]. Some users also distrust them because they fear losing control over how they sign in [F17].

## The crux: recovery and fallback paths

Passkeys move the problem to account recovery. When a device is lost, recovering access can be more complex than resetting a password [F16]. FIDO's recommended fix is to register multiple authenticators, which adds work for users [F14]. Many services add SMS or email recovery to cover this gap. Doing so can undermine FIDO2's security, because an attacker will target the weakest path [F13]. The same applies when SMS remains available for high-risk transactions: the passkey benefit is then only partial [F9]. Microsoft notes that traditional recovery methods, such as knowledge questions and round-trip codes, are clunky and invite impersonation [F18].

## Implications for banks

For banks, the evidence points to making passkeys the main login method. They resist phishing and SIM-swap attacks [F21][F2], and the reported data suggest they also reduce friction [F10][F11]. The security gain lasts only if recovery and step-up flows avoid falling back to SMS [F9][F13]. Banks would therefore need stronger recovery methods, such as several registered authenticators [F14] or identity verification [F18]. They would also need to keep supporting customers whose devices cannot use passkeys [F15][F1].

## Limitations

- Many sources are authentication vendors (Corbado, Authsignal, MojoAuth, LoginRadius) with a commercial interest in passkeys. Their performance figures are self-reported.
- Most speed and success-rate data compare passkeys with passwords or 'traditional MFA', not specifically with SMS OTP. Only one vendor source gave direct passkey-vs-SMS numbers [F10].
- The NIST assurance-level mapping comes from a secondary source, not the NIST document itself. The search budget ran out before primary regulatory sources (NIST, UAE central bank, etc.) could be checked.
- No bank-specific deployment studies were found, such as passkey enrolment rates among banking customers or fraud outcomes after rollout.
- The sources did not cover threats passkeys do not address: authorized push-payment scams, malware on an already-unlocked device, or compromise of the cloud account that syncs passkeys. These remain relevant to banking but are unverified here.
- Some cited pages carry 2026 dates and figures that could not be independently verified.

## References

- **[F1]** [Passkeys vs SMS OTP: Conversion, Cost & Security](https://www.corbado.com/blog/passkeys-vs-sms-otp): "SMS OTP keeps one real advantage: near-universal reach, since every phone can receive a text without setup."
- **[F2]** [Passkeys vs SMS OTP: Conversion, Cost & Security](https://www.corbado.com/blog/passkeys-vs-sms-otp): "An SMS OTP is a human-readable code, which makes it vulnerable to phishing, SIM-swap attacks and malware that reads incoming messages."
- **[F3]** [Passkeys vs SMS OTP: Conversion, Cost & Security](https://www.corbado.com/blog/passkeys-vs-sms-otp): "they cost almost nothing per login versus a per-message carrier fee"
- **[F4]** [SMS OTP bans are forcing a reset in banking authentication](https://nhimg.org/articles/sms-otp-bans-are-forcing-a-reset-in-banking-authentication): "Regulators in more than 25 markets are moving banks away from SMS one-time passwords"
- **[F5]** [SMS OTP bans are forcing a reset in banking authentication](https://nhimg.org/articles/sms-otp-bans-are-forcing-a-reset-in-banking-authentication): "the bank does not control the delivery path, so the code can be copied, redirected, or harvested through SIM swap"
- **[F6]** [What Are OTPs in Messages? SMS One-Time Passwords, Risks, and Safer Alternatives](https://mojoauth.com/blog/what-are-otps-in-messages-sms-risks): "SIM-swap fraud losses reported to the FBI Internet Crime Complaint Center climbed past $72 million in 2022 alone"
- **[F7]** [SIM swap fraud: How criminals hijack your phone and financial accounts](https://www.news24.com/business/money/sim-swap-fraud-how-criminals-hijack-your-phone-and-financial-accounts-20261015-1068): "When the bank issues a security OTP, it goes straight to the scammer."
- **[F8]** [What is the difference between SMS OTP and phishing-resistant passkeys for authentication security?](https://nhimg.org/faq/what-is-the-difference-between-sms-otp-and-phishing-resistant-passkeys-for-authe/): "SMS OTP can be defeated by relaying or coercing the code in real time."
- **[F9]** [What is the difference between SMS OTP and phishing-resistant passkeys for authentication security?](https://nhimg.org/faq/what-is-the-difference-between-sms-otp-and-phishing-resistant-passkeys-for-authe/): "If a platform supports passkeys but still lets users fall back to SMS for high-risk transactions, the security benefit is only partial."
- **[F10]** [SMS-based authentication: Why it’s no longer enough for security](https://www.authsignal.com/blog/articles/why-sms-based-authentication-is-no-longer-enough-for-secure-account-protection): "Average sign-in time drops to 14 seconds versus 23 seconds for SMS OTP, and first-try success rates hit 100% compared to 94% for SMS."
- **[F11]** [Passkey Adoption Statistics 2026: Sourced Figures](https://nhimg.org/passkey-adoption-statistics-guide): "the Index reports a 93% sign-in success rate for passkeys against 78% for passwords and traditional MFA."
- **[F12]** [Passkeys & Conversion: How Passkeys increase Login Success](https://www.corbado.com/blog/passkeys-increase-conversion): "sign-ins are on average 73% faster with passkeys than with passwords (8.5s with passkeys vs. 31.2s with passwords on average)"
- **[F13]** [Challenges and Potential Improvements for Passkey Adoption—A Literature Review with a User-Centric Perspective](https://dx.doi.org/10.3390/app15084414): "adding alternative recovery methods, such as email- or SMS-based account recovery, can undermine the increased security benefits of FIDO2"
- **[F14]** [Challenges and Potential Improvements for Passkey Adoption—A Literature Review with a User-Centric Perspective](https://dx.doi.org/10.3390/app15084414): "The FIDO Alliance’s official recommendation to achieve self-service recovery is to have multiple authenticators and keep one as a backup"
- **[F15]** [Passkeys: Benefits, limitations, and will they replace passwords?](https://specopssoft.com/blog/passkeys-benefits-limitations-passwords/): "Not all devices support passkeys, especially older or less capable devices."
- **[F16]** [Passkeys: Benefits, limitations, and will they replace passwords?](https://specopssoft.com/blog/passkeys-benefits-limitations-passwords/): "the recovery process can be more complex than with traditional passwords"
- **[F17]** [Challenges and Potential Improvements for Passkey Adoption—A Literature Review with a User-Centric Perspective](https://dx.doi.org/10.3390/app15084414): "may also make users hesitant to trust passkeys, fearing the loss of control over their authentication process"
- **[F18]** [Synced passkeys and high assurance account recovery](https://techcommunity.microsoft.com/blog/microsoft-entra-blog/synced-passkeys-and-high-assurance-account-recovery/3627343): "it’s ripe for impersonation attacks"
- **[F19]** [What is the difference between SMS OTP and phishing-resistant passkeys for authentication security?](https://nhimg.org/faq/what-is-the-difference-between-sms-otp-and-phishing-resistant-passkeys-for-authe/): "Phishing-resistant passkeys align with high-assurance authenticators."
- **[F20]** [What Are OTPs in Messages? SMS One-Time Passwords, Risks, and Safer Alternatives](https://mojoauth.com/blog/what-are-otps-in-messages-sms-risks): "smishing (a fake text drives you to a fake login page that captures both your password and your OTP in real"
- **[F21]** [FIDO Passkeys: Passwordless Authentication](https://fidoalliance.org/passkeys/): "Unlike passwords, passkeys are always strong and phishing-resistant"
- **[F22]** [SIM swap fraud: How criminals hijack your phone and financial accounts](https://www.news24.com/business/money/sim-swap-fraud-how-criminals-hijack-your-phone-and-financial-accounts-20261015-1068): "They claim your account is being hacked and offer to “fix it” if you read out the OTP"

---
*1 sub-questions, 1 research round(s), 22/22 findings passed checks, 22 cited. Cost $0.34, 89s.*
