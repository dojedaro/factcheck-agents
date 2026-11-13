# Passkeys vs. SMS Codes for Bank Logins: Security Trade-offs

> What are the security trade-offs between passkeys and SMS codes for bank logins?

On the available evidence, passkeys are the stronger login authenticator: NIST SP 800-63B-4 names SMS/voice out-of-band authentication as its only restricted authenticator [F1], while secondary sources say synced passkeys reach at least AAL2 and device-bound passkeys AAL3 [F8][F5]. SMS codes are not banned, though. NIST still allows them at AAL2 under conditions [F3], and PSD2, PCI DSS and India's RBI continue to accept or allow SMS OTP [F4]. The main caveat is that a passkey deployment's real strength depends on its recovery path. If a passkey can be restored with an SMS code, email link or a weakly verified help-desk call, attackers can target that channel, and the account may be only as strong as the fallback [F7][F10][F12].

## Bottom line

For bank logins, passkeys offer a higher assurance level than SMS codes. One secondary source places synced passkeys at AAL2 or above and device-bound passkeys at AAL3, with SMS codes at roughly AAL1 [F8]. Another secondary summary, which only partly supports its claim, also indicates that syncable passkeys can meet AAL2 while SMS OTP is restricted [F5]. That advantage can be lost if the bank keeps SMS or other weak channels as the passkey recovery path [F7][F12].

## How standards and regulators treat SMS codes

NIST SP 800-63B-4 names exactly one restricted authenticator: the use of the PSTN (SMS or voice) for out-of-band authentication [F1]. NIST says it may adjust this restricted status as the threat landscape and the PSTN's technical operation change [F2]. According to a secondary summary, restricted does not mean prohibited. SMS and voice codes remain allowed at AAL2 if the provider offers an alternative and explains the risk, but they are not allowed at AAL3 [F3].

The sources disagree on SMS's assurance level. One source puts SMS codes at roughly AAL1 [F8], while the NIST summary says they are still permitted at AAL2 with conditions [F3]. Outside NIST, a secondary source reports that PSD2 strong customer authentication accepts SMS OTP as a possession element, PCI DSS does not prohibit it, and India's RBI has kept it [F4]. Banks in these jurisdictions are therefore not forced off SMS, even though NIST signals that it is the weaker option.

## Why SMS is considered weaker

One source attributes NIST's restricted classification to SIM-swap and interception risk [F9]. This evidence only partly supports its claim, so it should be read as one source's explanation of NIST's reasoning, not as NIST's own words. A secondary summary also says code-based OTPs can be phished, because users can be tricked into typing codes on a fake site [F5]. That evidence was likewise only partly verified, and it speaks about OTPs such as TOTP in general, not SMS specifically.

## The recovery path is the key weakness for passkeys

Several sources stress that attackers tend to bypass passkeys through account recovery rather than by breaking the underlying cryptography [F7][F12].

- **SMS recovery:** One source argues that if a passkey can be restored with an SMS code, the account is only as strong as that SMS code [F7]. This claim was only partly verified. Leaving SMS recovery behind passkeys is described as a common deployment mistake [F9], though that evidence is also only partial.
- **Email recovery:** Recovery by email link makes the account depend on the security of the user's email account [F10].
- **Help desk recovery:** Fallbacks that accept emailed codes, SMS codes or lightly verified support requests let attackers go after the recovery channel instead of the passkey [F12].

On the usability side, one source says losing a device is usually recoverable because synced passkeys are replicated across the user's trusted ecosystem. It says the real failure mode is a weak fallback such as email or SMS OTP [F11], though this claim is only partly supported.

## Implications for bank deployments

Replacing SMS login codes with passkeys raises assurance on the primary login [F8]. To keep that gain, the evidence suggests not leaving SMS, email links or weakly verified help-desk resets as the recovery route, since those channels then set the effective security level [F7][F10][F12]. Banks that keep SMS for regulatory or reach reasons can rely on PSD2 and RBI acceptance [F4]. Under NIST's framing, however, they would need to offer an alternative and explain the risk to stay at AAL2 [F3].

## Limitations

- Most claims about AAL levels, regulatory treatment and recovery risk come from secondary or vendor sources, not the primary regulations. Only F1 and F2 quote NIST directly.
- The sources conflict on the assurance level of SMS. One places it at roughly AAL1 [F8], while another says NIST still permits it at AAL2 under conditions [F3].
- Secondary sources also disagree on when NIST introduced the restricted category, either in Rev 3 or first in Rev 4 [F6]. That evidence is only partly verified.
- Several key claims are only partly supported: SIM-swap and interception as NIST's stated rationale [F9], code phishability [F5], SMS recovery capping passkey strength [F7], and device-loss recoverability [F11].
- The evidence does not directly describe the mechanism that makes passkeys phishing-resistant. It also gives no empirical data on fraud or account-takeover rates for SMS versus passkeys at banks.
- No evidence covers user adoption, accessibility, cost, or customer-support burden. These are relevant trade-offs for banks but cannot be assessed here.
- Regulatory coverage is limited to NIST, PSD2, PCI DSS and RBI, and the non-NIST claims rely on a single secondary source [F4].

## References

- **[F1]** [NIST Special Publication 800-63B](https://pages.nist.gov/800-63-4/sp800-63b.html): "At the time of publication of these guidelines, there is one restricted authenticator: the **use of the PSTN for out-of-band authentication**"
- **[F2]** [NIST Special Publication 800-63B](https://pages.nist.gov/800-63-4/sp800-63b.html): "NIST may adjust the restricted status of out-of-band authentication using the PSTN based on the evolution of the threat landscape and the technical operation of the PSTN."
- **[F3]** [Is SMS OTP Still Allowed? NIST, PSD2, PCI DSS (2026)](https://www.broadnet.me/blog/sms-otp-security-standards-2026): "classes SMS and voice codes as a "restricted" authenticator that is still allowed at AAL2 if the provider offers an alternative and explains the risk, but not at AAL3"
- **[F4]** [Is SMS OTP Still Allowed? NIST, PSD2, PCI DSS (2026)](https://www.broadnet.me/blog/sms-otp-security-standards-2026): "PSD2 accepts it as a possession element, PCI DSS does not prohibit it and India's RBI kept it."
- **[F5]** [NIST SP 800-63-4 Is Final: What the New Digital Identity Guidelines Actually Change](https://authlayer.dev/blog/nist-800-63-4-authentication-requirements/) *(partially supported)*: "Syncable passkeys can meet AAL2. SMS OTP is restricted."
- **[F6]** [NIST SP 800-63-4 Is Final: What the New Digital Identity Guidelines Actually Change](https://authlayer.dev/blog/nist-800-63-4-authentication-requirements/) *(partially supported)*: "SP 800-63B rev 3 moved PSTN-based authenticators (SMS and voice OTP) into a “restricted” category"
- **[F7]** [Passkey Account Recovery: How Attackers Bypass Passkeys](https://www.corbado.com/blog/passkey-account-recovery-authenticate-2026) *(partially supported)*: "If a passkey can be restored with an SMS code, the account is only as strong as that SMS code"
- **[F8]** [Passkey Account Recovery: How Attackers Bypass Passkeys](https://www.corbado.com/blog/passkey-account-recovery-authenticate-2026): "Synced passkeys meet at least AAL2 and device-bound passkeys AAL3. SMS codes, email links, security questions and help desk calls sit at roughly AAL1."
- **[F9]** [Passkey Recovery and Lockout: The Complete Guide for Relying Parties - Security Boulevard](https://securityboulevard.com/2026/07/passkey-recovery-and-lockout-the-complete-guide-for-relying-parties/) *(partially supported)*: "NIST SP 800-63B classifies SMS as a restricted authenticator precisely because of SIM-swap and interception risk"
- **[F10]** [Passkey Recovery and Lockout: The Complete Guide for Relying Parties - Security Boulevard](https://securityboulevard.com/2026/07/passkey-recovery-and-lockout-the-complete-guide-for-relying-parties/): "your account security is only as strong as the user's email account"
- **[F11]** [Passkey recovery and device sync reduce lockout risk](https://nhimg.org/articles/passkey-recovery-and-device-sync-reduce-lockout-risk/) *(partially supported)*: "Passkey device loss is usually recoverable because synced passkeys are replicated across trusted ecosystems"
- **[F12]** [When does passkey recovery become a security weakness instead of a convenience?](https://nhimg.org/faq/when-does-passkey-recovery-become-a-security-weakness-instead-of-a-convenience/): "If the fallback accepts emailed codes, SMS codes, or lightly verified support requests, an attacker can attack the account by attacking the recovery channel"

---
*2 sub-questions, 1 research round(s), 12/12 findings passed checks, 12 cited. Cost $0.97, 106s.*
