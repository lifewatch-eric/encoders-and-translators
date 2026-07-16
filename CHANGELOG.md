# Changelog

All notable changes to this repository are documented here.  
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Added
- `EML211_to_EML220` — initial stable release of the EML 2.1.1 → 2.2.0 stylesheet
- `EML220_to_DataCite401` — skeleton stylesheet and mapping notes
- `ISO19139_to_EML220` — skeleton stylesheet and mapping notes
- `ISO19139_to_EOSC` — ISO 19139 → EOSC Resource "Service" (JSON) for EOSC Beyond onboarding; mapping sourced from `ISO19139_to_EOSC_profile.xlsx`, core fields implemented, several optional EOSC fields intentionally left unmapped — see the transformation's `docs/mapping-notes.md`
- `ISO19139_to_DataCite401` — ISO 19139 → DataCite 4.0.1 / OpenAIRE (`oaire:resource`) for Workflow and VRE resources, for the "Harvesting with OpenAIRE" program; mapping sourced from `ISO19139 - to - DataCite4.1.xlsx` ("Workflow" and "VRE" sheets), core fields implemented, creation date / revision date / status intentionally left unmapped — see the transformation's `docs/mapping-notes.md`
- `JSONLD_Mappings/EML_to_JSONLD` — EML 2.2.0 → schema.org JSON-LD (`Dataset`), Google Colab notebook (v5.2) with full PDF technical documentation
- `JSONLD_Mappings/ISO19139_to_JSONLD` — ISO 19139 → schema.org JSON-LD (`CreativeWork`/`Action`/`HowTo`, auto-detected), Google Colab notebook (v2.1) with full PDF technical documentation
- `shared/macros.xsl` — common named templates (`replace-string`, `normalize-date`, `is-empty-string`)
- `shared/namespaces.xml` — canonical namespace reference
- `ci/validate.sh` — automated validation script
- Repository-level `README.md`, `LICENSE` (MIT), `CHANGELOG.md`
- `docs/architecture.md`, `docs/contributing.md`, `docs/adding-a-transformation.md`
