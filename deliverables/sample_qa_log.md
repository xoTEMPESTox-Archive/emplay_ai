# Deliverable: Sample Q&A Log

This deliverable documents 10 representative natural-language questions executed against the indexed bid documents via the **RFP Intelligence Platform**, demonstrating query restructuring, addendum reconciliation, exact source citations (file name and page number), and factual guardrails.

---

## Question Set & Grounded Cited Answers

### Question 1: Submission Deadline with Addendum Override (Section 7.3 Benchmark)
- **Query:** *"What is the submission deadline for Bid1 after all addendums?"*
- **Bid ID:** `Bid1`
- **Cited Answer:**
  The final proposal submission deadline for Bid1 (Dallas ISD Solicitation JA-207652) is **July 9, 2024 at 2:00 PM CST**.
  
  The original solicitation schedule listed the due date as June 27, 2024 at 2:00 PM CST. **Addendum No. 2** formally extended and superseded the deadline, establishing July 9, 2024 at 2:00 PM CST as the new binding submission cutoff. All other terms and conditions remained unchanged.
- **Sources & Citations:**
  - `Addendum 2 RFP JA-207652 Student and Staff Computing Devices.pdf` (Page 1)
  - `JA-207652 Student and Staff Computing Devices FINAL.pdf` (Page 2)
- **Reconciliation Status:** Resolved by `AddendumReconciliationAgent` (Chronological hierarchy: Addendum 2 overrules Base RFP).

---

### Question 2: Required Affidavits (Section 7.3 Benchmark)
- **Query:** *"Which affidavits are required for the Dell laptop bid?"*
- **Bid ID:** `Bid2` (Resolved via Dynamic Catalog from *"Dell laptop bid"*)
- **Cited Answer:**
  For Bid2 (State of Maryland Dell Laptops w/ Extended Warranty), bidders are required to complete and submit the following mandatory legal documentation:
  1. **Contract Affidavit:** Mandatory certification covering vendor legal authority, registration with the State Department of Assessments and Taxation (SDAT), financial disclosure, and political contribution disclosures.
  2. **Mercury Affidavit:** Mandatory environmental certification affirming compliance with Maryland regulations regarding mercury-containing electrical equipment.
  3. **Warranty Affidavit / Certificate:** A warranty certificate or affidavit confirming the 3-year warranty on all machines purchased is required to be presented upon award.
- **Sources & Citations:**
  - `Contract_Affidavit.pdf` (Pages 1, 3)
  - `Mercury_Affidavit.pdf` (Page 1)
  - `PORFP_-_Dell_Laptop_Final.pdf` (Pages 2, 3)

---

### Question 3: Cross-Bid Warranty Comparison (Section 7.3 Benchmark)
- **Query:** *"Compare the warranty requirements of both bids."*
- **Bid ID:** Cross-Bid (`Bid1` & `Bid2`)
- **Cited Answer:**
  | Dimension | Bid1: Dallas ISD Student & Staff Devices | Bid2: Maryland Dell Laptops |
  | :--- | :--- | :--- |
  | **Duration** | Student Chromebooks: 1-year minimum OEM warranty.<br>Staff Laptops & Monitors: 3-year minimum OEM warranty. | 3 years warranty on all purchased laptops. |
  | **Effective Date** | Begins on the date equipment is formally placed into service by Dallas ISD. | 3 years following the date of delivery. |
  | **Repair SLA** | Warranty repairs/replacements completed at no cost within **five (5) business days** of reporting. | Standard 3-year warranty coverage. |
  | **Loaner Device** | If the 5-day repair SLA cannot be met, vendor must supply a temporary replacement device. | Not specified in solicitation. |
  | **Documentation** | Must equal or exceed warranty offered to the general public; list exclusions. | Warranty certificate or affidavit presented upon award. |
- **Sources & Citations:**
  - `JA-207652 Student and Staff Computing Devices FINAL.pdf` (Pages 4, 6, 8, 38)
  - `PORFP_-_Dell_Laptop_Final.pdf` (Page 3)
  - `Dell Laptops w_Extended Warranty - Bid Information - {3} _ BidNet Direct.html` (Page 1)

---

### Question 4: Bid Bond Requirements (Section 7.3 Benchmark)
- **Query:** *"Is a bid bond required, and if so, how much?"*
- **Bid ID:** General / Cross-Bid
- **Cited Answer:**
  **No bid bond is required for general proposal submissions.**
  
  Neither solicitation mandates an upfront bid bond, deposit, or cashier's check for standard vendor responses. In Bid1, bonding provisions only apply if an offeror submits as a Joint Venture (in which case joint venture performance and surety bonding in proportionate percentages is required). For Bid2, no bid bond or proposal guarantee is required.
- **Sources & Citations:**
  - `JA-207652 Student and Staff Computing Devices FINAL.pdf` (Page 52)
  - `Student and Staff Computing Devices __SOURCING #168884__ - Bid Information - {3} _ BidNet Direct.html` (Page 1)
  - `PORFP_-_Dell_Laptop_Final.pdf` (Page 1)

---

### Question 5: Addendum 2 Scope of Changes (Section 7.3 Benchmark)
- **Query:** *"What changed in Addendum 2 compared to the original RFP?"*
- **Bid ID:** `Bid1`
- **Cited Answer:**
  Addendum No. 2 for RFP JA-207652 had a single primary operational purpose:
  - **Due Date Extension:** Extended the RFP submission deadline from the original June 27, 2024 to **July 9, 2024 at 2:00 PM CST**.
  - **Preservation of Provisions:** The addendum explicitly confirmed that all other terms, conditions, specifications, and instructions in the original solicitation remained completely unchanged.
- **Sources & Citations:**
  - `Addendum 2 RFP JA-207652 Student and Staff Computing Devices.pdf` (Page 1)
  - `JA-207652 Student and Staff Computing Devices FINAL.pdf` (Page 2)

---

### Question 6: Hardware Specifications Comparison (Processor, RAM, Display)
- **Query:** *"What are the processor, RAM, and display specs for Bid1 vs Bid2?"*
- **Bid ID:** Cross-Bid (`Bid1` vs. `Bid2`)
- **Cited Answer:**
  - **Bid1 (Dallas ISD):** Structured as a multi-tier solicitation for district-wide student and staff devices (e.g., Tier 1 Small Student Chromebook, Tier 2 Large Student Chromebook, Tier 1 Basic Staff Laptop, Tier 2 Staff Laptop, Display Monitors - Touch and Non-Touch). Rather than specifying a single SKU, vendors must submit models meeting the district's minimum tier performance requirements.
  - **Bid2 (State of Maryland):** Specifies an exact hardware configuration for the **Dell Latitude 5550 XCTO Base**:
    - **Processor:** Intel Core Ultra 5 125U (12 MB cache, 12 cores, 14 threads, up to 4.3 GHz Turbo, Non-vPro).
    - **RAM:** 16 GB: 2 x 8 GB, DDR5, 5600 MT/s.
    - **Storage:** 256 GB, M.2 2230, TLC, Gen 4 PCIe NVMe SSD.
    - **Display:** 15.6", FHD 1920x1080, 60Hz, IPS, Non-Touch, Anti-Glare, 250 nit, 45% NTSC, with FHD RGB Camera.
- **Sources & Citations:**
  - `JA-207652 Student and Staff Computing Devices FINAL.pdf` (Pages 3, 37, 38, 40)
  - `Dell_Laptop_Specs.pdf` (Page 1)

---

### Question 7: Pre-Bid Meeting Attendance & Schedule
- **Query:** *"Is attendance at the pre-bid meeting mandatory for Bid1 and Bid2?"*
- **Bid ID:** Cross-Bid (`Bid1` & `Bid2`)
- **Cited Answer:**
  - **Bid1 (Dallas ISD):** A pre-bid conference was scheduled for **06/10/2024 at 03:00 PM EDT** via Microsoft Teams / electronic conference. Attendance was optional / non-mandatory, but recommended for prospective bidders.
  - **Bid2 (State of Maryland):** **None.** There was no pre-bid meeting or conference required for the Dell laptop procurement.
- **Sources & Citations:**
  - `Student and Staff Computing Devices __SOURCING #168884__ - Bid Information - {3} _ BidNet Direct.html` (Page 1)
  - `Dell Laptops w_Extended Warranty - Bid Information - {3} _ BidNet Direct.html` (Page 1)
  - `PORFP_-_Dell_Laptop_Final.pdf` (Page 2)

---

### Question 8: Submission Method & Platform
- **Query:** *"How must bids be submitted for both solicitations?"*
- **Bid ID:** Cross-Bid (`Bid1` & `Bid2`)
- **Cited Answer:**
  Both solicitations mandate electronic submissions via procurement portals:
  - **Bid1:** Must be submitted electronically through the **BidNet Direct** portal for Dallas ISD under Solicitation JA-207652. Sealed paper bids and emailed bids are not accepted.
  - **Bid2:** Master contractors must submit responses electronically through the Maryland state procurement portal (eMMA / BidNet Direct) in response to PORFP 001IT836371.
- **Sources & Citations:**
  - `Student and Staff Computing Devices __SOURCING #168884__ - Bid Information - {3} _ BidNet Direct.html` (Page 1)
  - `PORFP_-_Dell_Laptop_Final.pdf` (Page 1)

---

### Question 9: Manufacturer Authorization & Partner Standing
- **Query:** *"What manufacturer certifications or authorizations are required for Bid2?"*
- **Bid ID:** `Bid2`
- **Cited Answer:**
  For Bid2, bidders must be an authorized **Dell Master Contractor / Certified Partner** authorized under Maryland Statewide Contract 001B0600021 (IT Hardware Master Contract). Resellers must have valid manufacturer standing and warranty authorization to sell and service Dell commercial enterprise computing products.
- **Sources & Citations:**
  - `PORFP_-_Dell_Laptop_Final.pdf` (Pages 1, 2, 3)
  - `Dell Laptops w_Extended Warranty - Bid Information - {3} _ BidNet Direct.html` (Page 1)

---

### Question 10: Inquiries & Addendum 1 Scope
- **Query:** *"Did Addendum 1 extend the submission deadline for Bid1?"*
- **Bid ID:** `Bid1`
- **Cited Answer:**
  **No.** Addendum No. 1 explicitly addressed a prospective vendor's inquiry requesting a deadline extension and stated: *"Dallas ISD does not anticipate extending the submission deadline."* Addendum 1 addressed questions and timeline clarification without extending the date. It was subsequently **Addendum No. 2** that formally granted the extension to July 9, 2024.
- **Sources & Citations:**
  - `Addendum 1 RFP JA-207652 Student and Staff Computing Devices.pdf` (Page 1)
  - `Addendum 2 RFP JA-207652 Student and Staff Computing Devices.pdf` (Page 1)
