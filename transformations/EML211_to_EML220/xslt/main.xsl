<?xml version="1.0" encoding="UTF-8"?>
<!--
  ============================================================
  transformations/EML211_to_EML220/xslt/main.xsl
  ============================================================
  Upgrades an EML 2.1.1 document to EML 2.2.0.

  Transformation diagram:
    docs/transformation-diagram.svg
    docs/site/eml211-to-eml220.html

  Changelog:
    v1.4.0  2026-03-31
      - xsi:schemaLocation now produces STRICT, valid namespace→XSD pairs.
        Each namespace URI maps to its own authoritative schema location.
        The stylesheet parameter $schema-mode controls which XSD set to use:

          canonical (default) — EML 2.2.0 spec + CML.org stmml:
            Pair 1: https://eml.ecoinformatics.org/eml-2.2.0
                 →  https://eml.ecoinformatics.org/eml-2.2.0/eml.xsd
            Pair 2: http://www.xml-cml.org/schema/stmml-1.2
                 →  http://www.xml-cml.org/schema/stmml-1.2/stmml.xsd

          gbif — GBIF EML profile (if targeting GBIF/IPT):
            Pair 1: https://eml.ecoinformatics.org/eml-2.2.0
                 →  https://rs.gbif.org/schema/eml-gbif-profile/1.2/eml.xsd
            Pair 2: http://www.xml-cml.org/schema/stmml-1.2
                 →  https://rs.gbif.org/schema/eml-gbif-profile/1.2/stmml.xsd

        The previous output incorrectly copied the SOURCE document's
        schemaLocation verbatim and only updated the namespace URI token,
        leaving the XSD location pointing to the GBIF profile schema even
        in canonical mode. This is now completely rebuilt, not rewritten.

    v1.3.0  2026-03-31  stmml namespace prefix injection
    v1.2.0  2026-03-31  attribute deduplication
    v1.1.0  2026-03-30  8 bug fixes
    v1.0.0  2026-03-28  initial release

  Parameters:
    $package-id   (string, default 'newID')
      When set to any value other than 'newID', overwrites packageId.

    $schema-mode  (string, default 'canonical')
      Controls xsi:schemaLocation XSD target.
      Values: 'canonical' | 'gbif'

  Requirements: XSLT 1.0. Tested with Saxon-HE 12.x and lxml 6.x.

  Author:  LifeWatch ERIC Service Centre
  Version: 1.4.0  —  2026-03-31
  License: MIT
  ============================================================
-->
<xsl:stylesheet
    xmlns:xsl  ="http://www.w3.org/1999/XSL/Transform"
    xmlns:eml  ="https://eml.ecoinformatics.org/eml-2.2.0"
    xmlns:stmml="http://www.xml-cml.org/schema/stmml-1.2"
    exclude-result-prefixes="xsl"
    version="1.0">

  <xsl:output method="xml" encoding="UTF-8" indent="yes"/>

  <!-- ── Parameters ─────────────────────────────────────────────────────── -->
  <xsl:param name="package-id"  select="'newID'"/>
  <xsl:param name="schema-mode" select="'canonical'"/>

  <!--
    EML 2.2.0 namespace URIs (fixed, never change)
  -->
  <xsl:variable name="EML220_NS"   select="'https://eml.ecoinformatics.org/eml-2.2.0'"/>
  <xsl:variable name="STMML12_NS"  select="'http://www.xml-cml.org/schema/stmml-1.2'"/>

  <!--
    XSD locations — two modes:

    canonical: authoritative schemas from their namespace owners
      EML XSD  : https://eml.ecoinformatics.org/eml-2.2.0/eml.xsd
      stmml XSD: http://www.xml-cml.org/schema/stmml-1.2/stmml.xsd

    gbif: GBIF-hosted EML profile schemas (for GBIF/IPT submissions)
      EML XSD  : https://rs.gbif.org/schema/eml-gbif-profile/1.2/eml.xsd
      stmml XSD: https://rs.gbif.org/schema/eml-gbif-profile/1.2/stmml.xsd
  -->
  <xsl:variable name="EML_XSD_CANONICAL"   select="'https://eml.ecoinformatics.org/eml-2.2.0/eml.xsd'"/>
  <xsl:variable name="STMML_XSD_CANONICAL" select="'http://www.xml-cml.org/schema/stmml-1.2/stmml.xsd'"/>
  <xsl:variable name="EML_XSD_GBIF"        select="'https://rs.gbif.org/schema/eml-gbif-profile/1.2/eml.xsd'"/>
  <xsl:variable name="STMML_XSD_GBIF"      select="'https://rs.gbif.org/schema/eml-gbif-profile/1.2/stmml.xsd'"/>


  <!-- ============================================================
       NAMED TEMPLATE: build-schema-location
       Produces a strict namespace→XSD pair string based on $schema-mode.
       Format (two pairs, whitespace-separated):
         {eml-ns} {eml-xsd}
         {stmml-ns} {stmml-xsd}
       ============================================================ -->
  <xsl:template name="build-schema-location">
    <xsl:choose>
      <xsl:when test="$schema-mode = 'gbif'">
        <!-- GBIF profile pairs: namespace → GBIF-hosted XSD -->
        <xsl:value-of select="$EML220_NS"/>
        <xsl:text> </xsl:text>
        <xsl:value-of select="$EML_XSD_GBIF"/>
        <xsl:text> </xsl:text>
        <xsl:value-of select="$STMML12_NS"/>
        <xsl:text> </xsl:text>
        <xsl:value-of select="$STMML_XSD_GBIF"/>
      </xsl:when>
      <xsl:otherwise>
        <!-- canonical pairs: namespace → authoritative XSD from namespace owner -->
        <xsl:value-of select="$EML220_NS"/>
        <xsl:text> </xsl:text>
        <xsl:value-of select="$EML_XSD_CANONICAL"/>
        <xsl:text> </xsl:text>
        <xsl:value-of select="$STMML12_NS"/>
        <xsl:text> </xsl:text>
        <xsl:value-of select="$STMML_XSD_CANONICAL"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>


  <!-- ============================================================
       NAMED TEMPLATE: deduplicate-attributes
       Keeps only the FIRST occurrence of each <attributeName>.
       ============================================================ -->
  <xsl:template name="deduplicate-attributes">
    <xsl:param name="attributes"/>
    <xsl:param name="seen"     select="'|'"/>
    <xsl:param name="position" select="1"/>
    <xsl:variable name="count" select="count($attributes)"/>
    <xsl:if test="$position &lt;= $count">
      <xsl:variable name="current" select="$attributes[position() = $position]"/>
      <xsl:variable name="name"    select="normalize-space($current/attributeName)"/>
      <xsl:variable name="marker"  select="concat('|', $name, '|')"/>
      <xsl:choose>
        <xsl:when test="contains($seen, $marker)"/>
        <xsl:otherwise>
          <attribute>
            <xsl:copy-of select="$current/@*"/>
            <xsl:apply-templates select="$current/*"/>
          </attribute>
        </xsl:otherwise>
      </xsl:choose>
      <xsl:call-template name="deduplicate-attributes">
        <xsl:with-param name="attributes" select="$attributes"/>
        <xsl:with-param name="seen"       select="concat($seen, $marker)"/>
        <xsl:with-param name="position"   select="$position + 1"/>
      </xsl:call-template>
    </xsl:if>
  </xsl:template>


  <!-- ============================================================
       ROOT TEMPLATE
       ============================================================ -->
  <xsl:template match="/*">
    <xsl:element name="eml:eml">

      <!--
        Build xsi:schemaLocation from scratch — do NOT copy from source.
        Source may use wrong, outdated, or mixed schema locations.
        We always produce strict namespace→XSD pairs.
      -->
      <xsl:attribute name="xsi:schemaLocation"
                     namespace="http://www.w3.org/2001/XMLSchema-instance">
        <xsl:call-template name="build-schema-location"/>
      </xsl:attribute>

      <!-- Copy all root attributes except xsi:schemaLocation (rebuilt above) -->
      <xsl:for-each select="@*">
        <xsl:choose>

          <!-- Skip schemaLocation — already written above -->
          <xsl:when test="namespace-uri() = 'http://www.w3.org/2001/XMLSchema-instance'
                          and local-name() = 'schemaLocation'"/>

          <!-- ② packageId — honour override param -->
          <xsl:when test="name() = 'packageId'">
            <xsl:attribute name="{name()}" namespace="{namespace-uri()}">
              <xsl:choose>
                <xsl:when test="$package-id = 'newID'">
                  <xsl:value-of select="."/>
                </xsl:when>
                <xsl:otherwise>
                  <xsl:value-of select="$package-id"/>
                </xsl:otherwise>
              </xsl:choose>
            </xsl:attribute>
          </xsl:when>

          <!-- All other xsi:* attributes (noNamespaceSchemaLocation, etc.) -->
          <xsl:when test="namespace-uri() = 'http://www.w3.org/2001/XMLSchema-instance'">
            <xsl:attribute name="xsi:{local-name()}" namespace="{namespace-uri()}">
              <xsl:value-of select="."/>
            </xsl:attribute>
          </xsl:when>

          <!-- All remaining root attributes — copy verbatim -->
          <xsl:otherwise>
            <xsl:attribute name="{name()}" namespace="{namespace-uri()}">
              <xsl:value-of select="."/>
            </xsl:attribute>
          </xsl:otherwise>

        </xsl:choose>
      </xsl:for-each>

      <!-- Iterate direct children of root -->
      <xsl:for-each select="/*/*">
        <xsl:choose>
          <xsl:when test="name() = 'dataset'">
            <xsl:element name="{name(.)}" namespace="{namespace-uri(.)}">
              <xsl:copy-of select="@*"/>
              <xsl:apply-templates mode="dataset" select="."/>
            </xsl:element>
          </xsl:when>
          <xsl:otherwise>
            <xsl:element name="{name(.)}" namespace="{namespace-uri(.)}">
              <xsl:copy-of select="@*"/>
              <xsl:apply-templates mode="passthrough" select="."/>
            </xsl:element>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:for-each>

    </xsl:element>
  </xsl:template>


  <!-- ============================================================
       DATASET MODE
       ============================================================ -->
  <xsl:template mode="dataset" match="*">

    <!-- ③ alternateIdentifier — inject placeholder ONLY when source has none -->
    <xsl:choose>
      <xsl:when test="count(./alternateIdentifier) = 0">
        <alternateIdentifier/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:for-each select="./alternateIdentifier">
          <xsl:apply-templates select="."/>
        </xsl:for-each>
      </xsl:otherwise>
    </xsl:choose>

    <!-- ④ distribution — emit ONLY when at least one URL exists -->
    <xsl:variable name="gbif-urls"
      select="../additionalMetadata/metadata/gbif/physical[normalize-space(distribution/online/url) != '']"/>
    <xsl:variable name="entity-urls"
      select="../dataset/otherEntity/physical[normalize-space(distribution/online/url) != '']"/>
    <xsl:if test="count($gbif-urls) + count($entity-urls) &gt; 0">
      <distribution>
        <xsl:for-each select="$gbif-urls">
          <online>
            <xsl:if test="normalize-space(./objectName) != ''">
              <onlineDescription><xsl:value-of select="./objectName"/></onlineDescription>
            </xsl:if>
            <url><xsl:value-of select="./distribution/online/url"/></url>
          </online>
        </xsl:for-each>
        <xsl:for-each select="$entity-urls">
          <online>
            <xsl:if test="normalize-space(./objectName) != ''">
              <onlineDescription><xsl:value-of select="./objectName"/></onlineDescription>
            </xsl:if>
            <url><xsl:value-of select="./distribution/online/url"/></url>
          </online>
        </xsl:for-each>
      </distribution>
    </xsl:if>

    <!-- Iterate all dataset children -->
    <xsl:for-each select="./*">
      <xsl:choose>

        <!-- already emitted above -->
        <xsl:when test="name() = 'alternateIdentifier'"/>

        <!-- ⑤ pubDate — bare YYYY → YYYY-01-01 only; ISO 8601 passes through -->
        <xsl:when test="name() = 'pubDate'">
          <xsl:variable name="d" select="normalize-space(.)"/>
          <pubDate>
            <xsl:choose>
              <xsl:when test="string-length($d) = 4 and not(contains($d, '-'))">
                <xsl:value-of select="$d"/>
                <xsl:text>-01-01</xsl:text>
              </xsl:when>
              <xsl:otherwise>
                <xsl:value-of select="$d"/>
              </xsl:otherwise>
            </xsl:choose>
          </pubDate>
        </xsl:when>

        <!-- ⑥ dataTable — deduplicate attributeNames -->
        <xsl:when test="name() = 'dataTable'">
          <dataTable>
            <xsl:copy-of select="@*"/>
            <xsl:for-each select="./*">
              <xsl:choose>
                <xsl:when test="name() = 'attributeList'">
                  <attributeList>
                    <xsl:call-template name="deduplicate-attributes">
                      <xsl:with-param name="attributes" select="./attribute"/>
                      <xsl:with-param name="seen"       select="'|'"/>
                      <xsl:with-param name="position"   select="1"/>
                    </xsl:call-template>
                  </attributeList>
                </xsl:when>
                <xsl:otherwise>
                  <xsl:apply-templates select="."/>
                </xsl:otherwise>
              </xsl:choose>
            </xsl:for-each>
          </dataTable>
        </xsl:when>

        <!-- ⑦ project — copy ALL personnel fields faithfully -->
        <xsl:when test="name() = 'project'">
          <project>
            <title><xsl:value-of select="./title[1]"/></title>
            <xsl:for-each select="./personnel">
              <personnel>
                <xsl:apply-templates select="./*"/>
              </personnel>
            </xsl:for-each>
            <xsl:if test="./funding">
              <funding>
                <xsl:choose>
                  <xsl:when test="./funding/*">
                    <xsl:apply-templates select="./funding/*"/>
                  </xsl:when>
                  <xsl:otherwise>
                    <para><xsl:value-of select="./funding"/></para>
                  </xsl:otherwise>
                </xsl:choose>
              </funding>
            </xsl:if>
            <xsl:for-each select="./*[name()!='title' and name()!='personnel' and name()!='funding']">
              <xsl:apply-templates select="."/>
            </xsl:for-each>
          </project>
        </xsl:when>

        <!-- ⑧ methods — join multiple para, rewrap sampling -->
        <xsl:when test="name() = 'methods'">
          <methods>
            <xsl:for-each select="./methodStep">
              <methodStep>
                <xsl:for-each select="./description">
                  <description>
                    <para>
                      <xsl:for-each select="./para">
                        <xsl:value-of select="."/>
                        <xsl:if test="position() != last()">
                          <xsl:text> </xsl:text>
                        </xsl:if>
                      </xsl:for-each>
                    </para>
                  </description>
                </xsl:for-each>
                <xsl:for-each select="./instrumentation">
                  <instrumentation>
                    <xsl:for-each select="./instrument">
                      <instrument><xsl:value-of select="."/></instrument>
                    </xsl:for-each>
                  </instrumentation>
                </xsl:for-each>
                <xsl:for-each select="./software">
                  <software>
                    <title><xsl:value-of select="./title"/></title>
                    <version><xsl:value-of select="./version"/></version>
                  </software>
                </xsl:for-each>
              </methodStep>
            </xsl:for-each>
            <xsl:for-each select="./sampling">
              <sampling>
                <studyExtent>
                  <description>
                    <para><xsl:value-of select="./studyExtent/description/para"/></para>
                  </description>
                </studyExtent>
                <samplingDescription>
                  <para><xsl:value-of select="./samplingDescription/para"/></para>
                </samplingDescription>
              </sampling>
            </xsl:for-each>
          </methods>
        </xsl:when>

        <!-- ⑨ identity copy for all other dataset children -->
        <xsl:otherwise>
          <xsl:apply-templates select="."/>
        </xsl:otherwise>

      </xsl:choose>
    </xsl:for-each>
  </xsl:template>


  <!-- ============================================================
       PASSTHROUGH MODE  (access, citation, software, protocol)
       ============================================================ -->
  <xsl:template mode="passthrough" match="*">
    <xsl:for-each select="./*">
      <xsl:apply-templates select="."/>
    </xsl:for-each>
  </xsl:template>


  <!-- ============================================================
       IDENTITY COPY  (catch-all)
       ============================================================ -->
  <xsl:template match="*">
    <xsl:element name="{name(.)}" namespace="{namespace-uri(.)}">
      <xsl:copy-of select="@*"/>
      <xsl:apply-templates/>
    </xsl:element>
  </xsl:template>


  <!-- ============================================================
       replace-string — recursive XSLT 1.0 string substitution
       (retained for utility use by callers)
       ============================================================ -->
  <xsl:template name="replace-string">
    <xsl:param name="text"/>
    <xsl:param name="replace"/>
    <xsl:param name="with"/>
    <xsl:choose>
      <xsl:when test="contains($text, $replace)">
        <xsl:value-of select="substring-before($text, $replace)"/>
        <xsl:value-of select="$with"/>
        <xsl:call-template name="replace-string">
          <xsl:with-param name="text"    select="substring-after($text, $replace)"/>
          <xsl:with-param name="replace" select="$replace"/>
          <xsl:with-param name="with"    select="$with"/>
        </xsl:call-template>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="$text"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>


  <!-- ============================================================
       get-full-path — debug helper
       ============================================================ -->
  <xsl:template match="node()" mode="get-full-path">
    <xsl:for-each select="ancestor-or-self::*">
      <xsl:text>/</xsl:text>
      <xsl:value-of select="name()"/>
    </xsl:for-each>
  </xsl:template>

</xsl:stylesheet>
