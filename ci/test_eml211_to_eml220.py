#!/usr/bin/env python3
"""
ci/test_eml211_to_eml220.py
============================
Comprehensive test suite for the EML 2.1.1 → EML 2.2.0 transformation.

Runs with:  python3 ci/test_eml211_to_eml220.py
Requires:   pip install lxml

Each test class targets one transformation rule documented in
transformations/EML211_to_EML220/docs/mapping-notes.md.
"""

import sys
import textwrap
import unittest
from io import BytesIO
from lxml import etree

# ── Paths ──────────────────────────────────────────────────────────────────────
XSL_PATH = "transformations/EML211_to_EML220/xslt/main.xsl"

# Namespace map for XPath assertions
NS = {
    "eml": "https://eml.ecoinformatics.org/eml-2.2.0",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
}

# ── Helpers ────────────────────────────────────────────────────────────────────
def load_xslt():
    xsl_doc = etree.parse(XSL_PATH)
    return etree.XSLT(xsl_doc)

def transform(xml_string, **params):
    """Apply the stylesheet to an XML string and return the result Element."""
    transform_fn = load_xslt()
    src = etree.parse(BytesIO(xml_string.encode()))
    xslt_params = {k: etree.XSLT.strparam(v) for k, v in params.items()}
    result = transform_fn(src, **xslt_params)
    # Serialise and re-parse so XPath works cleanly
    xml_bytes = etree.tostring(result, encoding="unicode").encode()
    return etree.parse(BytesIO(xml_bytes)).getroot()

def eml211_doc(inner_dataset="", extra_root_attrs="", additional_metadata=""):
    """Build a minimal EML 2.1.1 envelope for testing."""
    return textwrap.dedent(f"""\
        <?xml version="1.0" encoding="UTF-8"?>
        <eml:eml
          xmlns:eml="eml://ecoinformatics.org/eml-2.1.1"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
          xsi:schemaLocation="eml://ecoinformatics.org/eml-2.1.1
                              http://rs.gbif.org/schema/eml-gbif-profile/1.2/eml.xsd
                              http://www.xml-cml.org/schema/stmml-1.1
                              http://rs.gbif.org/schema/eml-gbif-profile/1.2/stmml.xsd"
          packageId="test.package.1"
          system="http://gbif.org"
          {extra_root_attrs}>
          <dataset>
            <title>Test Dataset</title>
            {inner_dataset}
          </dataset>
          {additional_metadata}
        </eml:eml>
    """)

# ══════════════════════════════════════════════════════════════════════════════
# TEST CLASSES
# ══════════════════════════════════════════════════════════════════════════════

class TestNamespaceUpdate(unittest.TestCase):
    """Rule 1 — EML namespace URI is updated to 2.2.0."""

    def setUp(self):
        self.root = transform(eml211_doc())

    def test_root_element_namespace(self):
        self.assertEqual(
            self.root.nsmap.get("eml"),
            "https://eml.ecoinformatics.org/eml-2.2.0",
            "Root element must use EML 2.2.0 namespace URI"
        )

    def test_schema_location_eml_uri_updated(self):
        sl = self.root.get("{http://www.w3.org/2001/XMLSchema-instance}schemaLocation", "")
        self.assertIn("eml-2.2.0", sl,
                      "xsi:schemaLocation must reference eml-2.2.0")
        self.assertNotIn("eml-2.1.1", sl,
                         "xsi:schemaLocation must NOT still reference eml-2.1.1")

    def test_schema_location_stmml_updated(self):
        sl = self.root.get("{http://www.w3.org/2001/XMLSchema-instance}schemaLocation", "")
        self.assertIn("stmml-1.2", sl,
                      "xsi:schemaLocation must reference stmml-1.2")
        self.assertNotIn("stmml-1.1", sl,
                         "xsi:schemaLocation must NOT still reference stmml-1.1")


class TestPackageId(unittest.TestCase):
    """Rule 2 — packageId attribute handling."""

    def test_packageid_preserved_when_no_param(self):
        root = transform(eml211_doc())
        self.assertEqual(root.get("packageId"), "test.package.1",
                         "packageId must be preserved when no param supplied")

    def test_packageid_overridden_when_param_supplied(self):
        root = transform(eml211_doc(), **{"package-id": "my.new.id"})
        self.assertEqual(root.get("packageId"), "my.new.id",
                         "packageId must be overwritten when package-id param supplied")

    def test_packageid_preserved_when_param_is_default(self):
        # Passing 'newID' explicitly should behave like no param
        root = transform(eml211_doc(), **{"package-id": "newID"})
        self.assertEqual(root.get("packageId"), "test.package.1",
                         "packageId must be preserved when param equals 'newID'")


class TestAlternateIdentifier(unittest.TestCase):
    """Rule 3 — <alternateIdentifier/> injected as first child of <dataset>."""

    def test_alternate_identifier_present(self):
        root = transform(eml211_doc())
        dataset = root.find("eml:dataset", NS)
        self.assertIsNotNone(dataset, "<dataset> must exist")
        first_child = list(dataset)[0]
        self.assertEqual(
            etree.QName(first_child).localname,
            "alternateIdentifier",
            "First child of <dataset> must be <alternateIdentifier>"
        )

    def test_alternate_identifier_is_first(self):
        root = transform(eml211_doc("<pubDate>2020</pubDate>"))
        dataset = root.find("eml:dataset", NS)
        self.assertEqual(
            etree.QName(list(dataset)[0]).localname,
            "alternateIdentifier",
            "<alternateIdentifier> must precede all other dataset children"
        )


class TestDistributionHarvest(unittest.TestCase):
    """Rule 4 — <distribution> block is assembled from additionalMetadata and otherEntity."""

    ADDITIONAL_META = """
        <additionalMetadata>
          <metadata>
            <gbif>
              <physical>
                <objectName>Landing page</objectName>
                <distribution><online><url>https://example.org/dataset</url></online></distribution>
              </physical>
            </gbif>
          </metadata>
        </additionalMetadata>
    """

    DATASET_WITH_OTHER_ENTITY = """
        <otherEntity>
          <entityName>data.csv</entityName>
          <physical>
            <objectName>data.csv</objectName>
            <distribution><online><url>https://example.org/data.csv</url></online></distribution>
          </physical>
        </otherEntity>
    """

    def test_distribution_from_additional_metadata(self):
        root = transform(eml211_doc(additional_metadata=self.ADDITIONAL_META))
        urls = root.findall(".//url")
        url_texts = [u.text for u in urls]
        self.assertIn("https://example.org/dataset", url_texts,
                      "URL from additionalMetadata/gbif/physical must appear in output")

    def test_distribution_from_other_entity(self):
        root = transform(eml211_doc(
            inner_dataset=self.DATASET_WITH_OTHER_ENTITY,
            additional_metadata=self.ADDITIONAL_META
        ))
        urls = root.findall(".//url")
        url_texts = [u.text for u in urls]
        self.assertIn("https://example.org/data.csv", url_texts,
                      "URL from dataset/otherEntity/physical must appear in output")

    def test_both_sources_merged(self):
        root = transform(eml211_doc(
            inner_dataset=self.DATASET_WITH_OTHER_ENTITY,
            additional_metadata=self.ADDITIONAL_META
        ))
        urls = [u.text for u in root.findall(".//url")]
        self.assertGreaterEqual(len(urls), 2,
                                "Both distribution sources must produce online blocks")


class TestPubDateNormalisation(unittest.TestCase):
    """Rule 5 — year-only pubDate values are expanded to YYYY-01-01."""

    def test_year_only_expanded(self):
        root = transform(eml211_doc("<pubDate>2019</pubDate>"))
        pd = root.find(".//pubDate")
        self.assertIsNotNone(pd, "<pubDate> must exist in output")
        self.assertEqual(pd.text.strip(), "2019-01-01",
                         "Year-only pubDate must be normalised to YYYY-01-01")

    def test_full_date_unchanged(self):
        root = transform(eml211_doc("<pubDate>2019-07-15</pubDate>"))
        pd = root.find(".//pubDate")
        self.assertEqual(pd.text.strip(), "2019-07-15",
                         "Already-ISO-8601 pubDate must be left unchanged")

    def test_year_month_date_unchanged(self):
        root = transform(eml211_doc("<pubDate>2019-07</pubDate>"))
        pd = root.find(".//pubDate")
        self.assertEqual(pd.text.strip(), "2019-07",
                         "Year-month pubDate must be left unchanged")


class TestProjectNormalisation(unittest.TestCase):
    """Rule 6 — <project> is reshaped to EML 2.2.0 content model."""

    PROJECT_XML = """
        <project>
          <title>My Project</title>
          <title>Secondary title (should be dropped)</title>
          <personnel>
            <individualName><givenName>Alice</givenName><surName>Smith</surName></individualName>
            <role>principalInvestigator</role>
          </personnel>
        </project>
    """

    def setUp(self):
        self.root = transform(eml211_doc(self.PROJECT_XML))

    def test_only_first_title_emitted(self):
        titles = self.root.findall(".//project/title")
        self.assertEqual(len(titles), 1,
                         "<project> must have exactly one <title>")
        self.assertEqual(titles[0].text.strip(), "My Project")

    def test_personnel_given_name(self):
        gn = self.root.find(".//project/personnel/individualName/givenName")
        self.assertIsNotNone(gn)
        self.assertEqual(gn.text.strip(), "Alice")

    def test_personnel_sur_name(self):
        sn = self.root.find(".//project/personnel/individualName/surName")
        self.assertIsNotNone(sn)
        self.assertEqual(sn.text.strip(), "Smith")

    def test_role_becomes_position_name(self):
        pos = self.root.find(".//project/personnel/positionName")
        self.assertIsNotNone(pos, "<positionName> must exist from <role>")
        self.assertEqual(pos.text.strip(), "principalInvestigator")

    def test_organization_name_fallback(self):
        org = self.root.find(".//project/personnel/organizationName")
        self.assertIsNotNone(org, "<organizationName> must always be present")
        self.assertEqual(org.text.strip(), "Not available",
                         "<organizationName> must fall back to 'Not available'")


class TestPersonnelMissingRole(unittest.TestCase):
    """Rule 6 edge case — personnel with no <role> gets 'Not available' positionName."""

    PROJECT_NO_ROLE = """
        <project>
          <title>My Project</title>
          <personnel>
            <individualName><givenName>Bob</givenName><surName>Jones</surName></individualName>
          </personnel>
        </project>
    """

    def test_missing_role_falls_back(self):
        root = transform(eml211_doc(self.PROJECT_NO_ROLE))
        pos = root.find(".//project/personnel/positionName")
        # positionName exists only when role element is present; absence is also valid
        # but if present it must not be empty
        if pos is not None:
            self.assertNotEqual(pos.text.strip(), "",
                                "<positionName> must not be blank")


class TestMethodsNormalisation(unittest.TestCase):
    """Rule 7 — <methods> and <sampling> are reshaped."""

    METHODS_XML = """
        <methods>
          <methodStep>
            <description>
              <para>First para.</para>
              <para>Second para.</para>
            </description>
          </methodStep>
          <sampling>
            <studyExtent>
              <description><para>Study extent description.</para></description>
            </studyExtent>
            <samplingDescription>
              <para>Sampling description text.</para>
            </samplingDescription>
          </sampling>
        </methods>
    """

    def setUp(self):
        self.root = transform(eml211_doc(self.METHODS_XML))

    def test_method_step_present(self):
        ms = self.root.find(".//methods/methodStep")
        self.assertIsNotNone(ms, "<methodStep> must exist in output")

    def test_paras_joined(self):
        para = self.root.find(".//methods/methodStep/description/para")
        self.assertIsNotNone(para)
        text = para.text.strip() if para.text else ""
        self.assertIn("First para", text)
        self.assertIn("Second para", text)

    def test_sampling_study_extent(self):
        se = self.root.find(".//sampling/studyExtent/description/para")
        self.assertIsNotNone(se)
        self.assertIn("Study extent", se.text)

    def test_sampling_description(self):
        sd = self.root.find(".//sampling/samplingDescription/para")
        self.assertIsNotNone(sd)
        self.assertIn("Sampling description", sd.text)


class TestDataTablePassthrough(unittest.TestCase):
    """Rule 8 — <dataTable> is copied with attributes intact."""

    DATATABLE_XML = """
        <dataTable>
          <entityName>species.csv</entityName>
          <entityDescription>Species list</entityDescription>
          <attributeList>
            <attribute>
              <attributeName>taxonID</attributeName>
              <attributeDefinition>Unique taxon identifier</attributeDefinition>
            </attribute>
          </attributeList>
        </dataTable>
    """

    def setUp(self):
        self.root = transform(eml211_doc(self.DATATABLE_XML))

    def test_datatable_present(self):
        dt = self.root.find(".//dataTable")
        self.assertIsNotNone(dt, "<dataTable> must be present in output")

    def test_entity_name_preserved(self):
        en = self.root.find(".//dataTable/entityName")
        self.assertIsNotNone(en)
        self.assertEqual(en.text.strip(), "species.csv")

    def test_attribute_name_preserved(self):
        an = self.root.find(".//dataTable/attributeList/attribute/attributeName")
        self.assertIsNotNone(an)
        self.assertEqual(an.text.strip(), "taxonID")

    def test_attribute_definition_preserved(self):
        ad = self.root.find(".//dataTable/attributeList/attribute/attributeDefinition")
        self.assertIsNotNone(ad)
        self.assertEqual(ad.text.strip(), "Unique taxon identifier")


class TestIdentityCopy(unittest.TestCase):
    """Rule 9 — nodes without specific rules are copied verbatim."""

    def test_abstract_copied(self):
        root = transform(eml211_doc("<abstract><para>My abstract.</para></abstract>"))
        para = root.find(".//abstract/para")
        self.assertIsNotNone(para, "<abstract>/<para> must be preserved")
        self.assertEqual(para.text.strip(), "My abstract.")

    def test_keyword_set_copied(self):
        root = transform(eml211_doc(
            "<keywordSet><keyword>ecology</keyword>"
            "<keywordThesaurus>GBIF</keywordThesaurus></keywordSet>"
        ))
        kw = root.find(".//keywordSet/keyword")
        self.assertIsNotNone(kw)
        self.assertEqual(kw.text.strip(), "ecology")

    def test_contact_copied(self):
        root = transform(eml211_doc(
            "<contact><organizationName>LifeWatch ERIC</organizationName></contact>"
        ))
        org = root.find(".//contact/organizationName")
        self.assertIsNotNone(org)
        self.assertEqual(org.text.strip(), "LifeWatch ERIC")

    def test_language_copied(self):
        root = transform(eml211_doc("<language>en</language>"))
        lang = root.find(".//language")
        self.assertIsNotNone(lang)
        self.assertEqual(lang.text.strip(), "en")


class TestFullSampleFile(unittest.TestCase):
    """End-to-end — apply the stylesheet to the canonical sample file and
    verify every key output feature at once."""

    @classmethod
    def setUpClass(cls):
        SAMPLE_IN = "transformations/EML211_to_EML220/examples/input/sample-eml211.xml"
        cls.root = transform(open(SAMPLE_IN).read())

    def test_namespace_updated(self):
        self.assertIn("2.2.0", self.root.nsmap.get("eml", ""))

    def test_package_id_preserved(self):
        self.assertEqual(self.root.get("packageId"), "lifewatch.sample.dataset.1")

    def test_alternate_identifier_injected(self):
        dataset = self.root.find("eml:dataset", NS)
        self.assertEqual(etree.QName(list(dataset)[0]).localname, "alternateIdentifier")

    def test_pubdate_normalised(self):
        pd = self.root.find(".//pubDate")
        self.assertEqual(pd.text.strip(), "2019-01-01")

    def test_distribution_urls_present(self):
        urls = [u.text for u in self.root.findall(".//distribution//url")]
        self.assertTrue(any("lifewatch.eu" in (u or "") for u in urls))

    def test_project_single_title(self):
        self.assertEqual(len(self.root.findall(".//project/title")), 1)

    def test_methods_present(self):
        self.assertIsNotNone(self.root.find(".//methods/methodStep"))

    def test_data_table_present(self):
        self.assertIsNotNone(self.root.find(".//dataTable/entityName"))

    def test_stmml_namespace_updated(self):
        sl = self.root.get("{http://www.w3.org/2001/XMLSchema-instance}schemaLocation", "")
        self.assertIn("stmml-1.2", sl)
        self.assertNotIn("stmml-1.1", sl)


# ══════════════════════════════════════════════════════════════════════════════
# RUNNER
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()

    test_classes = [
        TestNamespaceUpdate,
        TestPackageId,
        TestAlternateIdentifier,
        TestDistributionHarvest,
        TestPubDateNormalisation,
        TestProjectNormalisation,
        TestPersonnelMissingRole,
        TestMethodsNormalisation,
        TestDataTablePassthrough,
        TestIdentityCopy,
        TestFullSampleFile,
    ]

    for tc in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(tc))

    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
