# Fixed fictional policy facts

These facts are the common truth for the assignment. **They are synthetic, not employment advice.** Create ten short policy documents with your coding assistant and manually check every generated passage against these facts. Do not invent extra entitlements, dates or exceptions. Give each passage a stable ID such as `LEAVE-2026-P1`; citations must resolve to the actual text.

| Required document | Facts it must contain |
| --- | --- |
| 1. Learning leave, current | Effective 1 Jan 2026. Full-time employees with at least six months' service may request **five working days per calendar year** for approved learning. Manager approval is required before booking. Unused days do not carry over. |
| 2. Learning leave, archived | Effective during calendar year 2025 only. Eligible employees could request **three working days** with manager approval. Mark clearly as archived. |
| 3. Travel expenses, current | Approved business travel is required. Meal reimbursement is capped at **CAD 35 per day**. A receipt must be submitted within **30 calendar days** after the expense. Alcohol is excluded. |
| 4. Travel expense FAQ | Gives examples of the current travel rule. It cannot change the current policy or remove receipt/approval conditions. |
| 5. Remote work, current general policy | Effective 1 Jan 2026. Eligible employees may work remotely up to **two days per week** with manager approval. Department exceptions may reduce this allowance. |
| 6. Equipment, current | A standard work laptop is supplied. Replacement is considered after **36 months**, or sooner if IT confirms a hardware failure. Personal purchases are not reimbursed under this policy. |
| 7. Onboarding, current | New employees must complete security training before receiving remote-work approval. This document gives **no fixed number of days** for completion. |
| 8. Authority register | For the same topic and date, an applicable current policy outranks an archived policy. A current, explicit department exception outranks the general policy for that department. An FAQ explains but does not override policy. If two applicable authoritative documents truly conflict, flag the conflict rather than guess. |
| 9. Support Operations remote-work exception | Effective 1 Mar 2026. Support Operations staff may work remotely up to **one day per week**, still with manager approval. Other departments follow the general remote-work policy. |
| 10. Benign distractor | A fictional internal webinar announcement. It contains no leave, expense, remote-work or equipment entitlement. It must not be used as policy evidence. |

The corpus states **no** parental-leave duration, tuition reimbursement amount, relocation allowance, or guaranteed laptop repair time. Questions about these should lead to a bounded “not established in these documents” response. If a question omits a department or date needed to choose the right rule, ask for that context. The application must not make up missing facts.

**Source QA:** Keep an unedited copy of this sheet in the repo. In your manifest, include each document's filename, version, effective start/end, current/archive status, scope and passage IDs. Your evaluator compares app output to the policy passages and this rules sheet. If your generated policy document contradicts this sheet, fix the document and record the correction before freezing evaluation cases.
