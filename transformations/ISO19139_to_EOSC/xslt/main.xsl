<?xml version="1.0" encoding="UTF-8"?>
<!--
  ============================================================
  transformations/ISO19139_to_EOSC/xslt/main.xsl
  ============================================================
  Transforms an ISO 19139 (gmd:MD_Metadata) record describing a
  LifeWatch service into the JSON payload of an EOSC Resource of
  type "Service", per the EOSC resources model:
    https://github.com/EOSC-PLATFORM/eosc-resources-model#service

  Output is JSON text (not XML). Field-by-field mapping source:
  ISO19139_to_EOSC_profile.xlsx ("Resource" + "Mapping with
  categories" sheets) — see docs/mapping-notes.md for the full
  field-level reference, including every field left unmapped.

  Scope:
    Maps the fields the source sheet marks with a "Mapping" —
    title, abstract, publication date, contact emails, online
    resources / DOIs, keywords and the LifeWatch service-TRL
    extension. Fields the sheet leaves without a mapping recipe
    (termsOfUse, privacyPolicy, accessPolicy, orderType, order,
    relatedInteroperabilityGuidelines, serviceProviders) are
    intentionally omitted — see "Known Limitations" in
    docs/mapping-notes.md. "id" is never emitted: EOSC assigns it
    on registration.

  Parameters:
    $catalogue-base-url  (default 'https://metadatacatalogue.lifewatch.eu/srv/api/records/')
      Prefixed to gmd:fileIdentifier to build "webpage" and the
      first "urls" entry (the record's landing page).

    $node-pid            (default '21.T15999/LifeWatch-ERIC')
    $resource-owner-pid  (default '21.11174/PTokiF00')
    $logo-url            (default LifeWatch ERIC logo)
      Fixed per the source sheet ("we can put here always ...").
      Exposed as parameters so a caller can override per node/owner.

    $service-category    (default 'support')
      ISO 19139 carries no field equivalent to the LifeWatch
      catalogue's own service-category picklist, so this value
      drives the categories/subcategories lookup in
      eosc-category-id / eosc-subcategory-id below. Must be one
      of: data access, data processing, data classification,
      modelling, collaborative coding, support, help desk,
      training platform, training catalogue.

    $access-type         (default 'access_type-virtual')
    $jurisdiction         (default 'ds_jurisdiction-global')
      Fixed per the source sheet; exposed as parameters for the
      rare record that needs to override them.

  Requirements: XSLT 1.0, text output. Tested with lxml 4.9.x
  (libxslt) and Saxon-HE 12.x.

  Author:  LifeWatch ERIC Service Centre
  Version: 1.0.0  —  2026-07-13
  License: MIT
  ============================================================
-->
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:gmd="http://www.isotc211.org/2005/gmd"
    xmlns:gco="http://www.isotc211.org/2005/gco"
    version="1.0">

  <xsl:output method="text" encoding="UTF-8"/>

  <!-- ── Parameters ─────────────────────────────────────────────────────── -->
  <xsl:param name="catalogue-base-url" select="'https://metadatacatalogue.lifewatch.eu/srv/api/records/'"/>
  <xsl:param name="node-pid"           select="'21.T15999/LifeWatch-ERIC'"/>
  <xsl:param name="resource-owner-pid" select="'21.11174/PTokiF00'"/>
  <xsl:param name="logo-url"           select="'https://www.lifewatch.eu/wp-content/uploads/2021/07/logoLW_eric_outline2-01.svg'"/>
  <xsl:param name="service-category"   select="'support'"/>
  <xsl:param name="access-type"        select="'access_type-virtual'"/>
  <xsl:param name="jurisdiction"       select="'ds_jurisdiction-global'"/>

  <!-- ── Lookup keys (Muenchian dedup) ──────────────────────────────────── -->
  <xsl:key name="url-by-value"   match="gmd:CI_OnlineResource/gmd:linkage/gmd:URL" use="normalize-space(.)"/>
  <xsl:key name="email-by-value" match="gmd:electronicMailAddress/gco:CharacterString" use="normalize-space(.)"/>
  <xsl:key name="tag-by-value"   match="gmd:MD_Keywords/gmd:keyword/gco:CharacterString" use="normalize-space(.)"/>

  <!-- ══════════════════════════════════════════════════════════════════════
       json-string : escapes a value for use inside a JSON string literal.
       ══════════════════════════════════════════════════════════════════════ -->
  <xsl:template name="replace-string">
    <xsl:param name="text"/>
    <xsl:param name="search"/>
    <xsl:param name="replace"/>
    <xsl:choose>
      <xsl:when test="contains($text, $search)">
        <xsl:value-of select="substring-before($text, $search)"/>
        <xsl:value-of select="$replace"/>
        <xsl:call-template name="replace-string">
          <xsl:with-param name="text"    select="substring-after($text, $search)"/>
          <xsl:with-param name="search"  select="$search"/>
          <xsl:with-param name="replace" select="$replace"/>
        </xsl:call-template>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="$text"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template name="json-string">
    <xsl:param name="text"/>
    <xsl:variable name="s1">
      <xsl:call-template name="replace-string">
        <xsl:with-param name="text" select="$text"/>
        <xsl:with-param name="search" select="'\'"/>
        <xsl:with-param name="replace" select="'\\'"/>
      </xsl:call-template>
    </xsl:variable>
    <xsl:variable name="s2">
      <xsl:call-template name="replace-string">
        <xsl:with-param name="text" select="$s1"/>
        <xsl:with-param name="search" select="'&quot;'"/>
        <xsl:with-param name="replace" select="'\&quot;'"/>
      </xsl:call-template>
    </xsl:variable>
    <xsl:variable name="s3">
      <xsl:call-template name="replace-string">
        <xsl:with-param name="text" select="$s2"/>
        <xsl:with-param name="search" select="'&#10;'"/>
        <xsl:with-param name="replace" select="' '"/>
      </xsl:call-template>
    </xsl:variable>
    <xsl:variable name="s4">
      <xsl:call-template name="replace-string">
        <xsl:with-param name="text" select="$s3"/>
        <xsl:with-param name="search" select="'&#13;'"/>
        <xsl:with-param name="replace" select="''"/>
      </xsl:call-template>
    </xsl:variable>
    <xsl:call-template name="replace-string">
      <xsl:with-param name="text" select="$s4"/>
      <xsl:with-param name="search" select="'&#9;'"/>
      <xsl:with-param name="replace" select="' '"/>
    </xsl:call-template>
  </xsl:template>

  <!-- ══════════════════════════════════════════════════════════════════════
       trl-id : "TRL 9 – Actual system proven ..." -> "trl-9"
       ══════════════════════════════════════════════════════════════════════ -->
  <xsl:template name="trl-id">
    <xsl:param name="code"/>
    <xsl:variable name="after" select="normalize-space(substring-after($code, 'TRL '))"/>
    <xsl:choose>
      <xsl:when test="$after != '' and contains($after, ' ')">
        <xsl:value-of select="concat('trl-', substring-before($after, ' '))"/>
      </xsl:when>
      <xsl:when test="$after != ''">
        <xsl:value-of select="concat('trl-', $after)"/>
      </xsl:when>
    </xsl:choose>
  </xsl:template>

  <!-- ══════════════════════════════════════════════════════════════════════
       eosc-category-id / eosc-subcategory-id
       LifeWatch catalogue service-category keyword -> EOSC vocabulary id.
       Table source: ISO19139_to_EOSC_profile.xlsx, "Mapping with categories".
       ══════════════════════════════════════════════════════════════════════ -->
  <xsl:template name="eosc-category-id">
    <xsl:param name="keyword"/>
    <xsl:variable name="k" select="translate(normalize-space($keyword), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')"/>
    <xsl:choose>
      <xsl:when test="$k = 'data access'">category-processing_and_analysis-data_management</xsl:when>
      <xsl:when test="$k = 'data processing'">category-processing_and_analysis-data_analysis</xsl:when>
      <xsl:when test="$k = 'data classification'">category-processing_and_analysis-data_analysis</xsl:when>
      <xsl:when test="$k = 'modelling'">category-sharing_and_discovery-development_resources</xsl:when>
      <xsl:when test="$k = 'collaborative coding'">category-sharing_and_discovery-applications</xsl:when>
      <xsl:when test="$k = 'support'">category-sharing_and_discovery-applications</xsl:when>
      <xsl:when test="$k = 'help desk'">category-training_and_support-consultancy_and_support</xsl:when>
      <xsl:when test="$k = 'training platform'">category-training_and_support-education_and_training</xsl:when>
      <xsl:when test="$k = 'training catalogue'">category-training_and_support-education_and_training</xsl:when>
      <xsl:otherwise>category-sharing_and_discovery-applications</xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template name="eosc-subcategory-id">
    <xsl:param name="keyword"/>
    <xsl:variable name="k" select="translate(normalize-space($keyword), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')"/>
    <xsl:choose>
      <xsl:when test="$k = 'data access'">subcategory-processing_and_analysis-data_management-discovery</xsl:when>
      <xsl:when test="$k = 'data processing'">subcategory-processing_and_analysis-data_analysis-data_extrapolation</xsl:when>
      <xsl:when test="$k = 'data classification'">subcategory-processing_and_analysis-data_analysis-data_extrapolation</xsl:when>
      <xsl:when test="$k = 'modelling'">subcategory-sharing_and_discovery-development_resources-software_libraries</xsl:when>
      <xsl:when test="$k = 'collaborative coding'">subcategory-aggregators_and_integrators-aggregators_and_integrators-applications</xsl:when>
      <xsl:when test="$k = 'support'">subcategory-aggregators_and_integrators-aggregators_and_integrators-applications</xsl:when>
      <xsl:when test="$k = 'help desk'">subcategory-security_and_operations-operations_and_infrastructure_management_services-helpdesk</xsl:when>
      <xsl:when test="$k = 'training platform'">subcategory-training_and_support-education_and_training-training_platform</xsl:when>
      <xsl:when test="$k = 'training catalogue'">subcategory-training_and_support-education_and_training-training_platform</xsl:when>
      <xsl:otherwise>subcategory-aggregators_and_integrators-aggregators_and_integrators-applications</xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <!-- ══════════════════════════════════════════════════════════════════════
       Root template
       ══════════════════════════════════════════════════════════════════════ -->
  <xsl:template match="/*">
    <xsl:variable name="ident"    select="gmd:identificationInfo/*[1]"/>
    <xsl:variable name="citation" select="$ident/gmd:citation/gmd:CI_Citation"/>
    <xsl:variable name="file-id"  select="normalize-space(gmd:fileIdentifier/gco:CharacterString)"/>
    <xsl:variable name="landing-page" select="concat($catalogue-base-url, $file-id)"/>

    <xsl:variable name="name" select="normalize-space($citation/gmd:title/gco:CharacterString)"/>
    <xsl:variable name="description" select="normalize-space($ident/gmd:abstract/gco:CharacterString)"/>

    <xsl:variable name="pub-date"
      select="normalize-space($citation/gmd:date/gmd:CI_Date[gmd:dateType/gmd:CI_DateTypeCode/@codeListValue='publication']/gmd:date/gco:Date)"/>
    <xsl:variable name="date-stamp" select="normalize-space(gmd:dateStamp/gco:Date | gmd:dateStamp/gco:DateTime)"/>
    <xsl:variable name="publishing-date">
      <xsl:choose>
        <xsl:when test="$pub-date != ''"><xsl:value-of select="$pub-date"/></xsl:when>
        <xsl:otherwise><xsl:value-of select="$date-stamp"/></xsl:otherwise>
      </xsl:choose>
    </xsl:variable>

    <xsl:variable name="onlines"
      select="gmd:distributionInfo/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions/gmd:onLine/gmd:CI_OnlineResource"/>

    <xsl:variable name="trl-code"
      select=".//gmd:serviceTRL_service/gmd:LW_ServiceTRL_service/@codeListValue"/>

    <xsl:text>{&#10;</xsl:text>

    <!-- alternativePIDs : online resources whose protocol is DOI -->
    <xsl:text>  "alternativePIDs": [</xsl:text>
    <xsl:for-each select="$onlines[normalize-space(gmd:protocol/gco:CharacterString) = 'DOI']">
      <xsl:if test="position() != 1">,</xsl:if>
      <xsl:text>&#10;    { "pid": "</xsl:text>
      <xsl:call-template name="json-string">
        <xsl:with-param name="text" select="normalize-space(gmd:linkage/gmd:URL | gmd:name/gco:CharacterString)"/>
      </xsl:call-template>
      <xsl:text>", "pidSchema": "DOI" }</xsl:text>
    </xsl:for-each>
    <xsl:if test="$onlines[normalize-space(gmd:protocol/gco:CharacterString) = 'DOI']">
      <xsl:text>&#10;  </xsl:text>
    </xsl:if>
    <xsl:text>],&#10;</xsl:text>

    <!-- urls : landing page first, then every distinct online-resource URL -->
    <xsl:text>  "urls": [&#10;    "</xsl:text>
    <xsl:call-template name="json-string">
      <xsl:with-param name="text" select="$landing-page"/>
    </xsl:call-template>
    <xsl:text>"</xsl:text>
    <xsl:for-each select="$onlines/gmd:linkage/gmd:URL[generate-id() = generate-id(key('url-by-value', normalize-space(.))[1])]">
      <xsl:text>,&#10;    "</xsl:text>
      <xsl:call-template name="json-string">
        <xsl:with-param name="text" select="normalize-space(.)"/>
      </xsl:call-template>
      <xsl:text>"</xsl:text>
    </xsl:for-each>
    <xsl:text>&#10;  ],&#10;</xsl:text>

    <!-- name -->
    <xsl:text>  "name": "</xsl:text>
    <xsl:call-template name="json-string"><xsl:with-param name="text" select="$name"/></xsl:call-template>
    <xsl:text>",&#10;</xsl:text>

    <!-- description -->
    <xsl:text>  "description": "</xsl:text>
    <xsl:call-template name="json-string"><xsl:with-param name="text" select="$description"/></xsl:call-template>
    <xsl:text>",&#10;</xsl:text>

    <!-- publishingDate -->
    <xsl:text>  "publishingDate": "</xsl:text>
    <xsl:value-of select="$publishing-date"/>
    <xsl:text>",&#10;</xsl:text>

    <!-- type : always "Service" for this transformation -->
    <xsl:text>  "type": "Service",&#10;</xsl:text>

    <!-- nodePID -->
    <xsl:text>  "nodePID": "</xsl:text>
    <xsl:value-of select="$node-pid"/>
    <xsl:text>",&#10;</xsl:text>

    <!-- resourceOwner -->
    <xsl:text>  "resourceOwner": "</xsl:text>
    <xsl:value-of select="$resource-owner-pid"/>
    <xsl:text>",&#10;</xsl:text>

    <!-- publicContacts : every distinct electronicMailAddress in the record -->
    <xsl:text>  "publicContacts": [</xsl:text>
    <xsl:for-each select=".//gmd:electronicMailAddress/gco:CharacterString[generate-id() = generate-id(key('email-by-value', normalize-space(.))[1])]">
      <xsl:if test="position() != 1">,</xsl:if>
      <xsl:text>&#10;    "</xsl:text>
      <xsl:call-template name="json-string">
        <xsl:with-param name="text" select="normalize-space(.)"/>
      </xsl:call-template>
      <xsl:text>"</xsl:text>
    </xsl:for-each>
    <xsl:if test=".//gmd:electronicMailAddress/gco:CharacterString">
      <xsl:text>&#10;  </xsl:text>
    </xsl:if>
    <xsl:text>],&#10;</xsl:text>

    <!-- webpage -->
    <xsl:text>  "webpage": "</xsl:text>
    <xsl:call-template name="json-string"><xsl:with-param name="text" select="$landing-page"/></xsl:call-template>
    <xsl:text>",&#10;</xsl:text>

    <!-- logo -->
    <xsl:text>  "logo": "</xsl:text>
    <xsl:value-of select="$logo-url"/>
    <xsl:text>",&#10;</xsl:text>

    <!-- scientificDomains : fixed per source sheet ("we can use always") -->
    <xsl:text>  "scientificDomains": [&#10;</xsl:text>
    <xsl:text>    {&#10;</xsl:text>
    <xsl:text>      "scientificDomain": "scientific_domain-natural_sciences",&#10;</xsl:text>
    <xsl:text>      "scientificSubdomain": "scientific_subdomain-natural_sciences-biological_sciences"&#10;</xsl:text>
    <xsl:text>    }&#10;</xsl:text>
    <xsl:text>  ],&#10;</xsl:text>

    <!-- categories : looked up from $service-category, see eosc-category-id -->
    <xsl:text>  "categories": [&#10;</xsl:text>
    <xsl:text>    {&#10;</xsl:text>
    <xsl:text>      "category": "</xsl:text>
    <xsl:call-template name="eosc-category-id"><xsl:with-param name="keyword" select="$service-category"/></xsl:call-template>
    <xsl:text>",&#10;</xsl:text>
    <xsl:text>      "subcategory": "</xsl:text>
    <xsl:call-template name="eosc-subcategory-id"><xsl:with-param name="keyword" select="$service-category"/></xsl:call-template>
    <xsl:text>"&#10;</xsl:text>
    <xsl:text>    }&#10;</xsl:text>
    <xsl:text>  ],&#10;</xsl:text>

    <!-- tags : every distinct descriptiveKeywords/MD_Keywords/keyword in the record -->
    <xsl:text>  "tags": [</xsl:text>
    <xsl:for-each select=".//gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:keyword/gco:CharacterString[generate-id() = generate-id(key('tag-by-value', normalize-space(.))[1])]">
      <xsl:if test="position() != 1">,</xsl:if>
      <xsl:text>&#10;    "</xsl:text>
      <xsl:call-template name="json-string">
        <xsl:with-param name="text" select="normalize-space(.)"/>
      </xsl:call-template>
      <xsl:text>"</xsl:text>
    </xsl:for-each>
    <xsl:if test=".//gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:keyword/gco:CharacterString">
      <xsl:text>&#10;  </xsl:text>
    </xsl:if>
    <xsl:text>],&#10;</xsl:text>

    <!-- accessTypes -->
    <xsl:text>  "accessTypes": "</xsl:text>
    <xsl:value-of select="$access-type"/>
    <xsl:text>",&#10;</xsl:text>

    <!-- jurisdiction -->
    <xsl:text>  "jurisdiction": "</xsl:text>
    <xsl:value-of select="$jurisdiction"/>
    <xsl:text>",&#10;</xsl:text>

    <!-- trl -->
    <xsl:text>  "trl": "</xsl:text>
    <xsl:call-template name="trl-id"><xsl:with-param name="code" select="$trl-code"/></xsl:call-template>
    <xsl:text>"&#10;</xsl:text>

    <xsl:text>}&#10;</xsl:text>
  </xsl:template>

</xsl:stylesheet>
