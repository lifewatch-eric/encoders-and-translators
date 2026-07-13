<?xml version="1.0" encoding="UTF-8"?>
<!--
  ============================================================
  transformations/ISO19139_to_EML220/xslt/main.xsl
  ============================================================
  Transforms an ISO 19139 (gmd:MD_Metadata) record into an
  EML 2.2.0 (eml:eml) dataset metadata document.

  Transformation diagram:
    docs/transformation-diagram.svg

  Scope:
    Maps the identification, responsible-party, keyword, extent,
    constraints and distribution blocks of ISO 19139 onto their
    EML 2.2.0 equivalents. dataTable / attribute-level metadata
    has no ISO 19139 counterpart and is out of scope — see
    docs/mapping-notes.md, "Known Limitations".

  Role mapping (gmd:CI_RoleCode -> EML party element):
    originator, author            -> dataset/creator
    (top-level) gmd:contact       -> dataset/metadataProvider
    pointOfContact (identification)-> dataset/contact
    any other cited role
      (publisher, custodian, ...) -> dataset/associatedParty
                                      with <role> set from the code

  Parameters:
    $package-id   (string, default '')
      Overrides packageId. When empty, gmd:fileIdentifier is used.

    $system       (string, default 'https://data.lifewatchitaly.eu')
      Value written to the eml:eml/@system attribute.

    $schema-mode  (string, default 'canonical')
      Controls xsi:schemaLocation XSD target.
      Values: 'canonical' | 'gbif'

  Requirements: XSLT 1.0. Tested with Saxon-HE 12.x and lxml 6.x.

  Author:  LifeWatch ERIC Service Centre
  Version: 1.0.0  —  2026-07-13
  License: MIT
  ============================================================
-->
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:gmd="http://www.isotc211.org/2005/gmd"
    xmlns:gco="http://www.isotc211.org/2005/gco"
    xmlns:gml="http://www.opengis.net/gml"
    exclude-result-prefixes="gmd gco gml"
    version="1.0">

  <xsl:output method="xml" encoding="UTF-8" indent="yes"/>

  <!-- ── Parameters ─────────────────────────────────────────────────────── -->
  <xsl:param name="package-id" select="''"/>
  <xsl:param name="system"     select="'https://data.lifewatchitaly.eu'"/>
  <xsl:param name="schema-mode" select="'canonical'"/>

  <xsl:variable name="EML220_NS"  select="'https://eml.ecoinformatics.org/eml-2.2.0'"/>
  <xsl:variable name="STMML12_NS" select="'http://www.xml-cml.org/schema/stmml-1.2'"/>
  <xsl:variable name="EML_XSD_CANONICAL"   select="'https://eml.ecoinformatics.org/eml-2.2.0/eml.xsd'"/>
  <xsl:variable name="STMML_XSD_CANONICAL" select="'http://www.xml-cml.org/schema/stmml-1.2/stmml.xsd'"/>
  <xsl:variable name="EML_XSD_GBIF"   select="'https://rs.gbif.org/schema/eml-gbif-profile/1.2/eml.xsd'"/>
  <xsl:variable name="STMML_XSD_GBIF" select="'https://rs.gbif.org/schema/eml-gbif-profile/1.2/stmml.xsd'"/>

  <xsl:variable name="UC" select="'ABCDEFGHIJKLMNOPQRSTUVWXYZ'"/>
  <xsl:variable name="LC" select="'abcdefghijklmnopqrstuvwxyz'"/>


  <!-- ============================================================
       NAMED TEMPLATE: build-schema-location
       ============================================================ -->
  <xsl:template name="build-schema-location">
    <xsl:choose>
      <xsl:when test="$schema-mode = 'gbif'">
        <xsl:value-of select="$EML220_NS"/><xsl:text> </xsl:text><xsl:value-of select="$EML_XSD_GBIF"/>
        <xsl:text> </xsl:text>
        <xsl:value-of select="$STMML12_NS"/><xsl:text> </xsl:text><xsl:value-of select="$STMML_XSD_GBIF"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="$EML220_NS"/><xsl:text> </xsl:text><xsl:value-of select="$EML_XSD_CANONICAL"/>
        <xsl:text> </xsl:text>
        <xsl:value-of select="$STMML12_NS"/><xsl:text> </xsl:text><xsl:value-of select="$STMML_XSD_CANONICAL"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>


  <!-- ============================================================
       NAMED TEMPLATE: iso639-to-word
       Maps common ISO 639-1/639-2 language codes to the full
       English name EML/GBIF consumers expect. Unknown codes pass
       through unchanged.
       ============================================================ -->
  <xsl:template name="iso639-to-word">
    <xsl:param name="code"/>
    <xsl:variable name="lower" select="translate(normalize-space($code), $UC, $LC)"/>
    <xsl:choose>
      <xsl:when test="$lower = 'eng' or $lower = 'en'">English</xsl:when>
      <xsl:when test="$lower = 'ita' or $lower = 'it'">Italian</xsl:when>
      <xsl:when test="$lower = 'fra' or $lower = 'fre' or $lower = 'fr'">French</xsl:when>
      <xsl:when test="$lower = 'deu' or $lower = 'ger' or $lower = 'de'">German</xsl:when>
      <xsl:when test="$lower = 'spa' or $lower = 'es'">Spanish</xsl:when>
      <xsl:when test="$lower = 'por' or $lower = 'pt'">Portuguese</xsl:when>
      <xsl:when test="$lower = 'nld' or $lower = 'dut' or $lower = 'nl'">Dutch</xsl:when>
      <xsl:when test="$lower = 'ell' or $lower = 'gre' or $lower = 'el'">Greek</xsl:when>
      <xsl:otherwise><xsl:value-of select="$code"/></xsl:otherwise>
    </xsl:choose>
  </xsl:template>


  <!-- ============================================================
       NAMED TEMPLATE: role-label
       Maps a gmd:CI_RoleCode value to an EML <role> free-text label
       for parties emitted as associatedParty.
       ============================================================ -->
  <xsl:template name="role-label">
    <xsl:param name="code"/>
    <xsl:choose>
      <xsl:when test="$code = 'publisher'">Publisher</xsl:when>
      <xsl:when test="$code = 'custodian'">Custodian</xsl:when>
      <xsl:when test="$code = 'distributor'">Distributor</xsl:when>
      <xsl:when test="$code = 'resourceProvider'">Resource Provider</xsl:when>
      <xsl:when test="$code = 'pointOfContact'">Point Of Contact</xsl:when>
      <xsl:when test="$code = 'principalInvestigator'">Principal Investigator</xsl:when>
      <xsl:when test="$code = 'processor'">Processor</xsl:when>
      <xsl:when test="$code = 'owner'">Owner</xsl:when>
      <xsl:when test="$code = 'user'">User</xsl:when>
      <xsl:when test="$code = 'coAuthor'">Co-Author</xsl:when>
      <xsl:when test="normalize-space($code) = ''">Associated Party</xsl:when>
      <xsl:otherwise><xsl:value-of select="$code"/></xsl:otherwise>
    </xsl:choose>
  </xsl:template>


  <!-- ============================================================
       NAMED TEMPLATE: last-word
       Recursively returns the final whitespace-delimited token.
       ============================================================ -->
  <xsl:template name="last-word">
    <xsl:param name="text"/>
    <xsl:choose>
      <xsl:when test="contains($text, ' ')">
        <xsl:call-template name="last-word">
          <xsl:with-param name="text" select="substring-after($text, ' ')"/>
        </xsl:call-template>
      </xsl:when>
      <xsl:otherwise><xsl:value-of select="$text"/></xsl:otherwise>
    </xsl:choose>
  </xsl:template>


  <!-- ============================================================
       NAMED TEMPLATES: family-name / given-name
       ISO 19139 carries a single gmd:individualName string. EML
       needs givenName/surName split apart.
         "Surname, Given"  -> split on the comma (preferred form)
         "Given Surname"   -> last token = surname (heuristic — see
                               Known Limitations for multi-word surnames)
         single token      -> treated as surname only
       ============================================================ -->
  <xsl:template name="family-name">
    <xsl:param name="full"/>
    <xsl:choose>
      <xsl:when test="contains($full, ',')">
        <xsl:value-of select="normalize-space(substring-before($full, ','))"/>
      </xsl:when>
      <xsl:when test="contains(normalize-space($full), ' ')">
        <xsl:call-template name="last-word">
          <xsl:with-param name="text" select="normalize-space($full)"/>
        </xsl:call-template>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="normalize-space($full)"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template name="given-name">
    <xsl:param name="full"/>
    <xsl:choose>
      <xsl:when test="contains($full, ',')">
        <xsl:value-of select="normalize-space(substring-after($full, ','))"/>
      </xsl:when>
      <xsl:when test="contains(normalize-space($full), ' ')">
        <xsl:variable name="norm" select="normalize-space($full)"/>
        <xsl:variable name="fam">
          <xsl:call-template name="last-word">
            <xsl:with-param name="text" select="$norm"/>
          </xsl:call-template>
        </xsl:variable>
        <xsl:value-of select="normalize-space(substring-before($norm, concat(' ', $fam)))"/>
      </xsl:when>
      <xsl:otherwise/>
    </xsl:choose>
  </xsl:template>


  <!-- ============================================================
       NAMED TEMPLATE: emit-party
       Renders the common EML "responsible party" fields
       (individualName/givenName+surName, organizationName,
       positionName, electronicMailAddress, optional role) from a
       gmd:CI_ResponsibleParty context node. Caller wraps the
       result in <creator>, <metadataProvider>, <contact> or
       <associatedParty>.
       ============================================================ -->
  <xsl:template name="emit-party">
    <xsl:param name="rp"/>
    <xsl:param name="role-text" select="''"/>
    <xsl:variable name="indiv" select="normalize-space($rp/gmd:individualName/gco:CharacterString)"/>
    <xsl:variable name="org"   select="normalize-space($rp/gmd:organisationName/gco:CharacterString)"/>
    <xsl:variable name="pos"   select="normalize-space($rp/gmd:positionName/gco:CharacterString)"/>
    <xsl:variable name="email" select="normalize-space($rp/gmd:contactInfo/gmd:CI_Contact/gmd:address/gmd:CI_Address/gmd:electronicMailAddress/gco:CharacterString)"/>

    <xsl:if test="$indiv != ''">
      <xsl:variable name="given">
        <xsl:call-template name="given-name"><xsl:with-param name="full" select="$indiv"/></xsl:call-template>
      </xsl:variable>
      <xsl:variable name="family">
        <xsl:call-template name="family-name"><xsl:with-param name="full" select="$indiv"/></xsl:call-template>
      </xsl:variable>
      <individualName>
        <xsl:if test="normalize-space($given) != ''">
          <givenName><xsl:value-of select="normalize-space($given)"/></givenName>
        </xsl:if>
        <surName><xsl:value-of select="normalize-space($family)"/></surName>
      </individualName>
    </xsl:if>

    <xsl:if test="$org != ''">
      <organizationName><xsl:value-of select="$org"/></organizationName>
    </xsl:if>

    <xsl:if test="$pos != ''">
      <positionName><xsl:value-of select="$pos"/></positionName>
    </xsl:if>

    <xsl:if test="$email != ''">
      <electronicMailAddress><xsl:value-of select="$email"/></electronicMailAddress>
    </xsl:if>

    <xsl:if test="$role-text != ''">
      <role><xsl:value-of select="$role-text"/></role>
    </xsl:if>
  </xsl:template>


  <!-- ============================================================
       ROOT TEMPLATE
       ============================================================ -->
  <xsl:template match="/*">
    <xsl:variable name="ident"    select="gmd:identificationInfo/gmd:MD_DataIdentification"/>
    <xsl:variable name="citation" select="$ident/gmd:citation/gmd:CI_Citation"/>

    <eml:eml
        xmlns:eml="https://eml.ecoinformatics.org/eml-2.2.0"
        xmlns:stmml="http://www.xml-cml.org/schema/stmml-1.2"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">

      <xsl:attribute name="xsi:schemaLocation" namespace="http://www.w3.org/2001/XMLSchema-instance">
        <xsl:call-template name="build-schema-location"/>
      </xsl:attribute>

      <xsl:attribute name="packageId">
        <xsl:choose>
          <xsl:when test="$package-id != ''"><xsl:value-of select="$package-id"/></xsl:when>
          <xsl:when test="normalize-space(gmd:fileIdentifier/gco:CharacterString) != ''">
            <xsl:value-of select="normalize-space(gmd:fileIdentifier/gco:CharacterString)"/>
          </xsl:when>
          <xsl:otherwise>unknown</xsl:otherwise>
        </xsl:choose>
      </xsl:attribute>
      <xsl:attribute name="system"><xsl:value-of select="$system"/></xsl:attribute>
      <xsl:attribute name="scope">system</xsl:attribute>

      <dataset>

        <!-- ① alternateIdentifier — every gmd:identifier under the citation -->
        <xsl:for-each select="$citation/gmd:identifier/gmd:MD_Identifier">
          <xsl:variable name="code" select="normalize-space(gmd:code/gco:CharacterString)"/>
          <xsl:if test="$code != ''">
            <alternateIdentifier><xsl:value-of select="$code"/></alternateIdentifier>
          </xsl:if>
        </xsl:for-each>

        <!-- ② title -->
        <title><xsl:value-of select="normalize-space($citation/gmd:title/gco:CharacterString)"/></title>

        <!-- ③ creator — citedResponsibleParty with role originator/author -->
        <xsl:for-each select="$citation/gmd:citedResponsibleParty/gmd:CI_ResponsibleParty
                               [translate(normalize-space(gmd:role/gmd:CI_RoleCode/@codeListValue), $UC, $LC) = 'originator'
                                or translate(normalize-space(gmd:role/gmd:CI_RoleCode/@codeListValue), $UC, $LC) = 'author']">
          <creator>
            <xsl:call-template name="emit-party"><xsl:with-param name="rp" select="."/></xsl:call-template>
          </creator>
        </xsl:for-each>

        <!-- ④ metadataProvider — top-level gmd:contact (the metadata record's own contact) -->
        <xsl:for-each select="gmd:contact/gmd:CI_ResponsibleParty">
          <metadataProvider>
            <xsl:call-template name="emit-party"><xsl:with-param name="rp" select="."/></xsl:call-template>
          </metadataProvider>
        </xsl:for-each>

        <!-- ⑤ associatedParty — every citedResponsibleParty that is NOT originator/author -->
        <xsl:for-each select="$citation/gmd:citedResponsibleParty/gmd:CI_ResponsibleParty
                               [not(translate(normalize-space(gmd:role/gmd:CI_RoleCode/@codeListValue), $UC, $LC) = 'originator'
                                    or translate(normalize-space(gmd:role/gmd:CI_RoleCode/@codeListValue), $UC, $LC) = 'author')]">
          <xsl:variable name="role-code" select="normalize-space(gmd:role/gmd:CI_RoleCode/@codeListValue)"/>
          <associatedParty>
            <xsl:call-template name="emit-party">
              <xsl:with-param name="rp" select="."/>
              <xsl:with-param name="role-text">
                <xsl:call-template name="role-label"><xsl:with-param name="code" select="$role-code"/></xsl:call-template>
              </xsl:with-param>
            </xsl:call-template>
          </associatedParty>
        </xsl:for-each>

        <!-- ⑥ pubDate — citation date typed 'publication', else metadata gmd:dateStamp -->
        <xsl:variable name="pub-date"
          select="normalize-space($citation/gmd:date/gmd:CI_Date
                   [translate(normalize-space(gmd:dateType/gmd:CI_DateTypeCode/@codeListValue), $UC, $LC) = 'publication']
                   /gmd:date/gco:Date)"/>
        <xsl:variable name="date-stamp" select="normalize-space(gmd:dateStamp/gco:Date | gmd:dateStamp/gco:DateTime)"/>
        <xsl:choose>
          <xsl:when test="$pub-date != ''"><pubDate><xsl:value-of select="$pub-date"/></pubDate></xsl:when>
          <xsl:when test="$date-stamp != ''"><pubDate><xsl:value-of select="$date-stamp"/></pubDate></xsl:when>
        </xsl:choose>

        <!-- ⑦ language — MD_DataIdentification/language, falls back to the top-level MD_Metadata/language -->
        <xsl:variable name="lang-code"
          select="normalize-space($ident/gmd:language/gmd:LanguageCode/@codeListValue
                   | /*/gmd:language/gmd:LanguageCode/@codeListValue)"/>
        <xsl:if test="$lang-code != ''">
          <language>
            <xsl:call-template name="iso639-to-word"><xsl:with-param name="code" select="$lang-code"/></xsl:call-template>
          </language>
        </xsl:if>

        <!-- ⑧ abstract -->
        <xsl:variable name="abs" select="normalize-space($ident/gmd:abstract/gco:CharacterString)"/>
        <xsl:if test="$abs != ''">
          <abstract><para><xsl:value-of select="$abs"/></para></abstract>
        </xsl:if>

        <!-- ⑨ keywordSet — one per gmd:MD_Keywords block -->
        <xsl:for-each select="$ident/gmd:descriptiveKeywords/gmd:MD_Keywords">
          <xsl:variable name="thesaurus" select="normalize-space(gmd:thesaurusName/gmd:CI_Citation/gmd:title/gco:CharacterString)"/>
          <keywordSet>
            <xsl:for-each select="gmd:keyword/gco:CharacterString">
              <keyword><xsl:value-of select="normalize-space(.)"/></keyword>
            </xsl:for-each>
            <keywordThesaurus>
              <xsl:choose>
                <xsl:when test="$thesaurus != ''"><xsl:value-of select="$thesaurus"/></xsl:when>
                <xsl:otherwise>none</xsl:otherwise>
              </xsl:choose>
            </keywordThesaurus>
          </keywordSet>
        </xsl:for-each>

        <!-- ⑩ intellectualRights — every useLimitation under resourceConstraints, one <para> each -->
        <xsl:variable name="rights-nodes" select="$ident/gmd:resourceConstraints/*/gmd:useLimitation/gco:CharacterString"/>
        <xsl:if test="$rights-nodes">
          <intellectualRights>
            <xsl:for-each select="$rights-nodes">
              <para><xsl:value-of select="normalize-space(.)"/></para>
            </xsl:for-each>
          </intellectualRights>
        </xsl:if>

        <!-- ⑪ distribution — gmd:onLine resources with a non-empty linkage URL -->
        <xsl:variable name="onlines"
          select="gmd:distributionInfo/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions
                   /gmd:onLine/gmd:CI_OnlineResource[normalize-space(gmd:linkage/gmd:URL) != '']"/>
        <xsl:if test="$onlines">
          <distribution>
            <xsl:for-each select="$onlines">
              <online>
                <xsl:variable name="nm" select="normalize-space(gmd:name/gco:CharacterString)"/>
                <xsl:if test="$nm != ''">
                  <onlineDescription><xsl:value-of select="$nm"/></onlineDescription>
                </xsl:if>
                <url><xsl:value-of select="normalize-space(gmd:linkage/gmd:URL)"/></url>
              </online>
            </xsl:for-each>
          </distribution>
        </xsl:if>

        <!-- ⑫ coverage — geographic bounding box(es) + temporal extent(s) -->
        <xsl:variable name="geo-boxes" select="$ident/gmd:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicBoundingBox"/>
        <xsl:variable name="temporal-extents" select="$ident/gmd:extent/gmd:EX_Extent/gmd:temporalElement/gmd:EX_TemporalExtent"/>
        <xsl:if test="$geo-boxes or $temporal-extents">
          <coverage>
            <xsl:for-each select="$geo-boxes">
              <xsl:variable name="geo-desc" select="normalize-space(../../gmd:description/gco:CharacterString)"/>
              <geographicCoverage>
                <geographicDescription>
                  <xsl:choose>
                    <xsl:when test="$geo-desc != ''"><xsl:value-of select="$geo-desc"/></xsl:when>
                    <xsl:otherwise>Not provided</xsl:otherwise>
                  </xsl:choose>
                </geographicDescription>
                <boundingCoordinates>
                  <westBoundingCoordinate><xsl:value-of select="normalize-space(gmd:westBoundLongitude/gco:Decimal)"/></westBoundingCoordinate>
                  <eastBoundingCoordinate><xsl:value-of select="normalize-space(gmd:eastBoundLongitude/gco:Decimal)"/></eastBoundingCoordinate>
                  <northBoundingCoordinate><xsl:value-of select="normalize-space(gmd:northBoundLatitude/gco:Decimal)"/></northBoundingCoordinate>
                  <southBoundingCoordinate><xsl:value-of select="normalize-space(gmd:southBoundLatitude/gco:Decimal)"/></southBoundingCoordinate>
                </boundingCoordinates>
              </geographicCoverage>
            </xsl:for-each>
            <xsl:for-each select="$temporal-extents">
              <temporalCoverage>
                <xsl:choose>
                  <xsl:when test="gmd:extent/gml:TimePeriod">
                    <rangeOfDates>
                      <beginDate><calendarDate><xsl:value-of select="normalize-space(gmd:extent/gml:TimePeriod/gml:beginPosition)"/></calendarDate></beginDate>
                      <endDate><calendarDate><xsl:value-of select="normalize-space(gmd:extent/gml:TimePeriod/gml:endPosition)"/></calendarDate></endDate>
                    </rangeOfDates>
                  </xsl:when>
                  <xsl:when test="gmd:extent/gml:TimeInstant">
                    <singleDateTime>
                      <calendarDate><xsl:value-of select="normalize-space(gmd:extent/gml:TimeInstant/gml:timePosition)"/></calendarDate>
                    </singleDateTime>
                  </xsl:when>
                </xsl:choose>
              </temporalCoverage>
            </xsl:for-each>
          </coverage>
        </xsl:if>

        <!-- ⑬ contact — MD_DataIdentification/pointOfContact (resource-level contact, any role) -->
        <xsl:for-each select="$ident/gmd:pointOfContact/gmd:CI_ResponsibleParty">
          <contact>
            <xsl:call-template name="emit-party"><xsl:with-param name="rp" select="."/></xsl:call-template>
          </contact>
        </xsl:for-each>

      </dataset>
    </eml:eml>
  </xsl:template>

</xsl:stylesheet>
