<?xml version="1.0" encoding="UTF-8"?>
<!--
  ============================================================
  transformations/ISO19139_to_DataCite401/xslt/main.xsl
  ============================================================
  Transforms an ISO 19139 (gmd:MD_Metadata) record describing a
  LifeWatch Workflow or Virtual Research Environment (VRE) into
  an OpenAIRE / DataCite 4.0.1 resource description
  (oaire:resource), for the "Harvesting with OpenAIRE" program.

  Field-by-field mapping source: "ISO19139 - to - DataCite4.1.xlsx"
  ("Workflow" and "VRE" sheets — INPUT/OUTPUT/COMMENTS columns).
  See docs/mapping-notes.md for the full reference, including every
  row the source sheet marks "Not mapped".

  Sibling transformation: EML220_to_DataCite401 targets the same
  oaire:resource / datacite: output vocabulary from an EML 2.2.0
  source for Dataset resources. This stylesheet targets the same
  vocabulary directly from ISO 19139 for Workflow / VRE resources —
  element order and attribute conventions (creatorName nameType=
  "Personal", rightsList shape, ...) intentionally match it.

  Scope:
    Maps fileIdentifier, title, abstract, the publication-typed
    citation date, responsible parties (routed to creator/
    contributor per the source sheet's 11-role table), the license
    useLimitation, keywords, and — when present — a DOI found among
    the distribution online resources. creation date, revision date
    and status are marked "Not mapped" in the source sheet and are
    intentionally omitted — see Known Limitations.

  Parameters:
    $resource-type      (default 'Workflow')
      Selects the fixed datacite:resourceType / oaire:resourceType
      pair. Values: 'Workflow' | 'VRE' (case-insensitive).

    $default-publisher   (default 'LifeWatch ERIC')
    $catalogue-base-url  (default 'https://metadatacatalogue.lifewatch.eu/srv/api/records/')
      Used to build a fallback datacite:identifier (identifierType
      "URL") when no DOI is found among the distribution online
      resources — DataCite requires a primary identifier and the
      source sheet leaves this case as an open question (see
      row "distribution info", COMMENTS column).

  Requirements: XSLT 1.0. Tested with Saxon-HE 12.x and lxml 4.9.x.

  Author:  LifeWatch ERIC Service Centre
  Version: 1.0.0  —  2026-07-13
  License: MIT
  ============================================================
-->
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:gmd="http://www.isotc211.org/2005/gmd"
    xmlns:gco="http://www.isotc211.org/2005/gco"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:datacite="http://datacite.org/schema/kernel-4"
    xmlns:vc="http://www.w3.org/2007/XMLSchema-versioning"
    xmlns:oaire="http://namespace.openaire.eu/schema/oaire/"
    exclude-result-prefixes="gmd gco"
    version="1.0">

  <xsl:output method="xml" encoding="UTF-8" indent="yes"/>

  <!-- ── Parameters ─────────────────────────────────────────────────────── -->
  <xsl:param name="resource-type"      select="'Workflow'"/>
  <xsl:param name="default-publisher"  select="'LifeWatch ERIC'"/>
  <xsl:param name="catalogue-base-url" select="'https://metadatacatalogue.lifewatch.eu/srv/api/records/'"/>

  <xsl:variable name="UC" select="'ABCDEFGHIJKLMNOPQRSTUVWXYZ'"/>
  <xsl:variable name="LC" select="'abcdefghijklmnopqrstuvwxyz'"/>

  <!-- ══════════════════════════════════════════════════════════════════════
       family-name / given-name : "Given Surname" -> split on last whitespace.
       "Surname, Given" -> split on comma. Same heuristic as
       ISO19139_to_EML220 (see that stylesheet's Known Limitations).
       ══════════════════════════════════════════════════════════════════════ -->
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

  <xsl:template name="family-name">
    <xsl:param name="full"/>
    <xsl:variable name="norm" select="normalize-space($full)"/>
    <xsl:choose>
      <xsl:when test="contains($norm, ',')">
        <xsl:value-of select="normalize-space(substring-before($norm, ','))"/>
      </xsl:when>
      <xsl:when test="contains($norm, ' ')">
        <xsl:call-template name="last-word">
          <xsl:with-param name="text" select="$norm"/>
        </xsl:call-template>
      </xsl:when>
      <xsl:otherwise><xsl:value-of select="$norm"/></xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template name="given-name">
    <xsl:param name="full"/>
    <xsl:variable name="norm" select="normalize-space($full)"/>
    <xsl:choose>
      <xsl:when test="contains($norm, ',')">
        <xsl:value-of select="normalize-space(substring-after($norm, ','))"/>
      </xsl:when>
      <xsl:when test="contains($norm, ' ')">
        <xsl:variable name="fam">
          <xsl:call-template name="last-word">
            <xsl:with-param name="text" select="$norm"/>
          </xsl:call-template>
        </xsl:variable>
        <xsl:value-of select="normalize-space(substring-before($norm, concat(' ', $fam)))"/>
      </xsl:when>
    </xsl:choose>
  </xsl:template>

  <!-- ══════════════════════════════════════════════════════════════════════
       party-target : gmd:role/CI_RoleCode/@codeListValue -> "creator" or a
       DataCite contributorType, per the source sheet's routing table.
       "originator" is not in the source sheet's table (it only appears in
       the VRE worked example) — routed to contributorType "Other" as a
       documented fallback, see Known Limitations.
       ══════════════════════════════════════════════════════════════════════ -->
  <xsl:template name="party-target">
    <xsl:param name="role"/>
    <xsl:variable name="r" select="translate(normalize-space($role), $UC, $LC)"/>
    <xsl:choose>
      <xsl:when test="$r = 'author'">creator</xsl:when>
      <xsl:when test="$r = 'creator'">creator</xsl:when>
      <xsl:when test="$r = 'owner'">creator</xsl:when>
      <xsl:when test="$r = 'associatedparty' or $r = 'associated party'">contributor:RelatedPerson</xsl:when>
      <xsl:when test="$r = 'custodian'">contributor:DataManager</xsl:when>
      <xsl:when test="$r = 'distributor'">contributor:Distributor</xsl:when>
      <xsl:when test="$r = 'pointofcontact' or $r = 'point of contact'">contributor:ContactPerson</xsl:when>
      <xsl:when test="$r = 'principalinvestigator' or $r = 'principal investigator'">contributor:Supervisor</xsl:when>
      <xsl:when test="$r = 'processor'">contributor:DataCurator</xsl:when>
      <xsl:when test="$r = 'resourceprovider' or $r = 'resource provider'">contributor:Producer</xsl:when>
      <xsl:when test="$r = 'user'">contributor:Researcher</xsl:when>
      <xsl:otherwise>contributor:Other</xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <!-- ══════════════════════════════════════════════════════════════════════
       license-uri : best-effort SPDX id -> canonical license URL.
       Only CC-BY-4.0 is proven by the source sheet's worked example; the
       rest follow its COMMENTS instruction ("put the right link according
       to the license if possible, e.g. GPL-3.0") on a best-effort basis.
       ══════════════════════════════════════════════════════════════════════ -->
  <xsl:template name="license-uri">
    <xsl:param name="license"/>
    <xsl:variable name="l" select="translate(normalize-space($license), $UC, $LC)"/>
    <xsl:choose>
      <xsl:when test="$l = 'cc-by-4.0' or $l = 'cc by 4.0'">https://creativecommons.org/licenses/by/4.0/</xsl:when>
      <xsl:when test="$l = 'cc-by-sa-4.0'">https://creativecommons.org/licenses/by-sa/4.0/</xsl:when>
      <xsl:when test="$l = 'cc0-1.0' or $l = 'cc0'">https://creativecommons.org/publicdomain/zero/1.0/</xsl:when>
      <xsl:when test="$l = 'mit'">https://opensource.org/license/mit/</xsl:when>
      <xsl:when test="$l = 'apache-2.0'">https://www.apache.org/licenses/LICENSE-2.0</xsl:when>
      <xsl:when test="$l = 'gpl-3.0'">https://www.gnu.org/licenses/gpl-3.0.html</xsl:when>
      <xsl:otherwise></xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <!-- ══════════════════════════════════════════════════════════════════════
       emit-party : renders one creator or contributor block.
       ══════════════════════════════════════════════════════════════════════ -->
  <xsl:template name="emit-party">
    <xsl:param name="rp"/>
    <xsl:param name="target"/>
    <xsl:variable name="indiv" select="normalize-space($rp/gmd:individualName/gco:CharacterString)"/>
    <xsl:variable name="org"   select="normalize-space($rp/gmd:organisationName/gco:CharacterString)"/>
    <xsl:variable name="email" select="normalize-space($rp/gmd:contactInfo/gmd:CI_Contact/gmd:address/gmd:CI_Address/gmd:electronicMailAddress/gco:CharacterString)"/>
    <xsl:variable name="given">
      <xsl:if test="$indiv != ''">
        <xsl:call-template name="given-name"><xsl:with-param name="full" select="$indiv"/></xsl:call-template>
      </xsl:if>
    </xsl:variable>
    <xsl:variable name="family">
      <xsl:if test="$indiv != ''">
        <xsl:call-template name="family-name"><xsl:with-param name="full" select="$indiv"/></xsl:call-template>
      </xsl:if>
    </xsl:variable>
    <xsl:variable name="display-name">
      <xsl:choose>
        <xsl:when test="$indiv != ''"><xsl:value-of select="concat($family, ', ', $given)"/></xsl:when>
        <xsl:otherwise><xsl:value-of select="$org"/></xsl:otherwise>
      </xsl:choose>
    </xsl:variable>

    <xsl:choose>
      <xsl:when test="$target = 'creator'">
        <datacite:creator>
          <datacite:creatorName nameType="Personal"><xsl:value-of select="$display-name"/></datacite:creatorName>
          <xsl:if test="$indiv != ''">
            <datacite:givenName><xsl:value-of select="$given"/></datacite:givenName>
            <datacite:familyName><xsl:value-of select="$family"/></datacite:familyName>
          </xsl:if>
          <xsl:if test="$org != ''">
            <datacite:affiliation><xsl:value-of select="$org"/></datacite:affiliation>
          </xsl:if>
        </datacite:creator>
      </xsl:when>
      <xsl:otherwise>
        <datacite:contributor contributorType="{substring-after($target, ':')}">
          <datacite:contributorName nameType="Personal"><xsl:value-of select="$display-name"/></datacite:contributorName>
          <xsl:if test="$org != ''">
            <datacite:affiliation><xsl:value-of select="$org"/></datacite:affiliation>
          </xsl:if>
        </datacite:contributor>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <!-- ══════════════════════════════════════════════════════════════════════
       Root template
       ══════════════════════════════════════════════════════════════════════ -->
  <xsl:template match="/*">
    <xsl:variable name="ident"    select="gmd:identificationInfo/*[1]"/>
    <xsl:variable name="citation" select="$ident/gmd:citation/gmd:CI_Citation"/>
    <xsl:variable name="file-id"  select="normalize-space(gmd:fileIdentifier/gco:CharacterString)"/>

    <xsl:variable name="title"    select="normalize-space($citation/gmd:title/gco:CharacterString)"/>
    <xsl:variable name="abstract" select="normalize-space($ident/gmd:abstract/gco:CharacterString)"/>
    <xsl:variable name="pub-date"
      select="normalize-space($citation/gmd:date/gmd:CI_Date[gmd:dateType/gmd:CI_DateTypeCode/@codeListValue='publication']/gmd:date/gco:Date)"/>

    <xsl:variable name="onlines"
      select="gmd:distributionInfo/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions/gmd:onLine/gmd:CI_OnlineResource"/>
    <xsl:variable name="doi-online"
      select="$onlines[normalize-space(gmd:protocol/gco:CharacterString) = 'DOI'
                        or contains(gmd:linkage/gmd:URL, 'doi.org')][1]"/>

    <xsl:variable name="license-text"
      select="normalize-space($ident/gmd:resourceConstraints/*/gmd:useLimitation/gco:CharacterString)"/>

    <xsl:variable name="rt" select="translate(normalize-space($resource-type), $UC, $LC)"/>

    <oaire:resource
        xsi:schemaLocation="http://namespace.openaire.eu/schema/oaire/
          https://www.openaire.eu/schema/repo-lit/4.0/openaire.xsd">

      <!-- Primary identifier: DOI if found among distribution online
           resources, else a catalogue-landing-page URL fallback so the
           (DataCite-mandatory) primary identifier is never empty. The
           source sheet leaves non-DOI distribution links unaddressed
           (see docs/mapping-notes.md, Known Limitations). -->
      <xsl:choose>
        <xsl:when test="$doi-online">
          <datacite:identifier identifierType="DOI">
            <xsl:value-of select="normalize-space($doi-online/gmd:linkage/gmd:URL)"/>
          </datacite:identifier>
        </xsl:when>
        <xsl:otherwise>
          <datacite:identifier identifierType="URL">
            <xsl:value-of select="concat($catalogue-base-url, $file-id)"/>
          </datacite:identifier>
        </xsl:otherwise>
      </xsl:choose>

      <datacite:alternateIdentifiers>
        <datacite:alternateIdentifier alternateIdentifierType="PackageID">
          <xsl:value-of select="$file-id"/>
        </datacite:alternateIdentifier>
      </datacite:alternateIdentifiers>

      <datacite:titles>
        <datacite:title xml:lang="en"><xsl:value-of select="$title"/></datacite:title>
      </datacite:titles>

      <datacite:publisher><xsl:value-of select="$default-publisher"/></datacite:publisher>

      <!-- publicationYear: not an explicit row in the source sheet, but
           derived here from the same publication date already mapped so
           the (DataCite-mandatory) field is never empty — see
           docs/mapping-notes.md. -->
      <xsl:if test="string-length($pub-date) &gt;= 4">
        <datacite:publicationYear><xsl:value-of select="substring($pub-date, 1, 4)"/></datacite:publicationYear>
      </xsl:if>

      <xsl:if test="$pub-date != ''">
        <datacite:dates>
          <datacite:date dateType="Issued"><xsl:value-of select="$pub-date"/></datacite:date>
        </datacite:dates>
      </xsl:if>

      <xsl:if test="$abstract != ''">
        <datacite:descriptions>
          <datacite:description descriptionType="Abstract"><xsl:value-of select="$abstract"/></datacite:description>
        </datacite:descriptions>
      </xsl:if>

      <datacite:subjects>
        <xsl:for-each select=".//gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:keyword/gco:CharacterString">
          <datacite:subject><xsl:value-of select="normalize-space(.)"/></datacite:subject>
        </xsl:for-each>
      </datacite:subjects>

      <datacite:creators>
        <xsl:for-each select=".//gmd:CI_ResponsibleParty">
          <xsl:variable name="role" select="normalize-space(gmd:role/gmd:CI_RoleCode/@codeListValue)"/>
          <xsl:variable name="target">
            <xsl:call-template name="party-target"><xsl:with-param name="role" select="$role"/></xsl:call-template>
          </xsl:variable>
          <xsl:if test="$target = 'creator'">
            <xsl:call-template name="emit-party">
              <xsl:with-param name="rp" select="."/>
              <xsl:with-param name="target" select="$target"/>
            </xsl:call-template>
          </xsl:if>
        </xsl:for-each>
      </datacite:creators>

      <datacite:contributors>
        <xsl:for-each select=".//gmd:CI_ResponsibleParty">
          <xsl:variable name="role" select="normalize-space(gmd:role/gmd:CI_RoleCode/@codeListValue)"/>
          <xsl:variable name="target">
            <xsl:call-template name="party-target"><xsl:with-param name="role" select="$role"/></xsl:call-template>
          </xsl:variable>
          <xsl:if test="$target != 'creator'">
            <xsl:call-template name="emit-party">
              <xsl:with-param name="rp" select="."/>
              <xsl:with-param name="target" select="$target"/>
            </xsl:call-template>
          </xsl:if>
        </xsl:for-each>
      </datacite:contributors>

      <!-- resourceType : fixed pair per $resource-type ('Workflow' | 'VRE') -->
      <xsl:choose>
        <xsl:when test="$rt = 'vre'">
          <datacite:resourceType resourceTypeGeneral="InteractiveResource"></datacite:resourceType>
          <oaire:resourceType resourceTypeGeneral="other research product"
              uri="http://purl.org/coar/resource_type/c_e9a0">interactive resource</oaire:resourceType>
        </xsl:when>
        <xsl:otherwise>
          <datacite:resourceType resourceTypeGeneral="Workflow"></datacite:resourceType>
          <oaire:resourceType resourceTypeGeneral="other research product"
              uri="http://purl.org/coar/resource_type/c_393c">workflow</oaire:resourceType>
        </xsl:otherwise>
      </xsl:choose>

      <!-- rightsList : useLimitation text, rightsURI resolved best-effort -->
      <xsl:if test="$license-text != ''">
        <xsl:variable name="uri">
          <xsl:call-template name="license-uri"><xsl:with-param name="license" select="$license-text"/></xsl:call-template>
        </xsl:variable>
        <datacite:rightsList>
          <xsl:choose>
            <xsl:when test="normalize-space($uri) != ''">
              <datacite:rights rightsURI="{normalize-space($uri)}"
                  rightsIdentifier="{$license-text}" rightsIdentifierScheme="SPDX">open access</datacite:rights>
            </xsl:when>
            <xsl:otherwise>
              <datacite:rights rightsIdentifier="{$license-text}" rightsIdentifierScheme="SPDX">open access</datacite:rights>
            </xsl:otherwise>
          </xsl:choose>
        </datacite:rightsList>
      </xsl:if>

    </oaire:resource>
  </xsl:template>

</xsl:stylesheet>
