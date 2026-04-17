<?xml version="1.0" encoding="UTF-8"?>
<!--
  ============================================================
  transformations/EML220_to_DataCite401/xslt/main.xsl
  ============================================================
  Transforms an EML 2.2.0 metadata record to an OpenAIRE /
  DataCite 4.0.1 resource description (oaire:resource).

  Produced for LifeWatch ERIC to expose dataset metadata via
  OAI-PMH → OpenAIRE → EOSC portal onboarding pipeline.

  Changelog:
    v1.2.0  2026-04-15
      - FIX-A  Explicit DOI selection: first alternateIdentifier
               containing 'doi' (case-insensitive). No last-wins risk.
      - FIX-B  Non-DOI identifiers (handle, UUID) now emitted in
               datacite:alternateIdentifiers, not silently dropped.
      - FIX-C  Publisher = $default-publisher (LifeWatch ERIC) always.
               Creator org is NOT the publisher — it goes in affiliation.
      - FIX-D  publicationYear guard: empty pubDate no longer emits
               an invalid empty element.
      - FIX-E  xml:lang normalised to ISO 639-1 ('en' not 'English').
      - FIX-F  datacite:rightsList wrapper added (required by DataCite 4.x).
      - FIX-G  Temporal coverage mapped to datacite:date[@dateType='Collected'].
               Supports both singleDateTime and rangeOfDates (ISO 8601 interval).
      - FIX-H  datacite:sizes from dataTable/physical/size.
      - FIX-I  datacite:formats detected from fieldDelimiter / objectName.
      - FIX-J  oaire:file now carries @mimeType and @objectType attributes.
      - FIX-K  datacite:fundingReferences from project/funding.
      - FIX-L  datacite:creatorName / contributorName carry @nameType="Personal".
               datacite:givenName / datacite:familyName sub-elements added.

    v1.1.0  2026-04-14  12 bug fixes (FIX-1 through FIX-12)
    v1.0.0  2025        Original — Lucia Vaira, LifeWatch ERIC

  Parameters:
    $default-publisher  (string, default 'LifeWatch ERIC')
      The institution that makes the resource available (catalogue owner).
      DataCite defines publisher as "the entity that holds, archives,
      publishes, prints, distributes, releases, issues, or produces
      the resource." This is LifeWatch ERIC, NOT the creator's org.

    $catalogue-url  (string)
      Base URL for catalogue record links when no DOI is present.

  Requirements: XSLT 1.0. Tested with Saxon-HE 12.x and lxml 6.x.

  Original author : Lucia Vaira (lucia.vaira@lifewatch.eu), LifeWatch ERIC
  Revised by      : LifeWatch ERIC Service Centre
  Version         : 1.2.0  — 2026-04-15
  License         : CC-BY-4.0
  ============================================================
-->
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    version="1.0">

  <xsl:output method="xml" encoding="UTF-8" indent="yes"/>

  <xsl:param name="default-publisher" select="'LifeWatch ERIC'"/>
  <xsl:param name="catalogue-url"
    select="'https://metadatacatalogue.lifewatch.eu/srv/eng/catalog.search#/metadata/'"/>

  <xsl:variable name="UC" select="'ABCDEFGHIJKLMNOPQRSTUVWXYZ'"/>
  <xsl:variable name="LC" select="'abcdefghijklmnopqrstuvwxyz'"/>


  <!-- ============================================================
       NAMED TEMPLATE: iso-lang (FIX-E)
       Maps full language names to ISO 639-1 2-letter codes.
       ============================================================ -->
  <xsl:template name="iso-lang">
    <xsl:param name="lang"/>
    <xsl:variable name="lower" select="translate(normalize-space($lang), $UC, $LC)"/>
    <xsl:choose>
      <xsl:when test="$lower = 'english'  or $lower = 'en'">en</xsl:when>
      <xsl:when test="$lower = 'italian'  or $lower = 'it'">it</xsl:when>
      <xsl:when test="$lower = 'french'   or $lower = 'fr'">fr</xsl:when>
      <xsl:when test="$lower = 'german'   or $lower = 'de'">de</xsl:when>
      <xsl:when test="$lower = 'spanish'  or $lower = 'es'">es</xsl:when>
      <xsl:when test="$lower = 'portuguese' or $lower = 'pt'">pt</xsl:when>
      <xsl:when test="$lower = 'dutch'    or $lower = 'nl'">nl</xsl:when>
      <xsl:when test="$lower = 'greek'    or $lower = 'el'">el</xsl:when>
      <xsl:otherwise><xsl:value-of select="$lower"/></xsl:otherwise>
    </xsl:choose>
  </xsl:template>


  <!-- ============================================================
       ROOT TEMPLATE
       ============================================================ -->
  <xsl:template match="/*">
    <oaire:resource
        xmlns:xsi      ="http://www.w3.org/2001/XMLSchema-instance"
        xmlns:rdf      ="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
        xmlns:dc       ="http://purl.org/dc/elements/1.1/"
        xmlns:datacite ="http://datacite.org/schema/kernel-4"
        xmlns:vc       ="http://www.w3.org/2007/XMLSchema-versioning"
        xmlns:oaire    ="http://namespace.openaire.eu/schema/oaire/"
        xsi:schemaLocation="http://namespace.openaire.eu/schema/oaire/
          https://www.openaire.eu/schema/repo-lit/4.0/openaire.xsd">

      <xsl:for-each select="./dataset">

        <!-- ── FIX-A: Explicit DOI identifier selection ──────────────
             Takes the FIRST alternateIdentifier containing 'doi'.
             The preceding-sibling guard ensures first-occurrence only.
        ─────────────────────────────────────────────────────────────── -->
        <xsl:variable name="doi-id">
          <xsl:for-each select="./alternateIdentifier">
            <xsl:if test="contains(translate(normalize-space(.), $UC, $LC), 'doi')
                          and not(preceding-sibling::alternateIdentifier[
                            contains(translate(normalize-space(.), $UC, $LC), 'doi')])">
              <xsl:value-of select="normalize-space(.)"/>
            </xsl:if>
          </xsl:for-each>
        </xsl:variable>

        <!-- First non-DOI identifier (handle, UUID, plain URL) -->
        <xsl:variable name="handle-id">
          <xsl:for-each select="./alternateIdentifier">
            <xsl:if test="not(contains(translate(normalize-space(.), $UC, $LC), 'doi'))
                          and not(preceding-sibling::alternateIdentifier[
                            not(contains(translate(normalize-space(.), $UC, $LC), 'doi'))])">
              <xsl:value-of select="normalize-space(.)"/>
            </xsl:if>
          </xsl:for-each>
        </xsl:variable>

        <xsl:variable name="pkg-id" select="normalize-space(//@packageId)"/>

        <!-- Primary identifier -->
        <xsl:choose>
          <xsl:when test="normalize-space($doi-id) != ''">
            <datacite:identifier identifierType="DOI">
              <xsl:value-of select="$doi-id"/>
            </datacite:identifier>
          </xsl:when>
          <xsl:when test="normalize-space($handle-id) != ''">
            <datacite:identifier identifierType="URL">
              <xsl:value-of select="concat($catalogue-url, $handle-id)"/>
            </datacite:identifier>
          </xsl:when>
          <xsl:otherwise>
            <datacite:identifier identifierType="URL">
              <xsl:value-of select="concat($catalogue-url, $pkg-id)"/>
            </datacite:identifier>
          </xsl:otherwise>
        </xsl:choose>

        <!-- ── FIX-B: Non-DOI identifiers in alternateIdentifiers ────
             When DOI is the primary identifier, preserve the handle/URL
             and packageId so nothing is silently dropped.
        ─────────────────────────────────────────────────────────────── -->
        <xsl:if test="normalize-space($doi-id) != '' and normalize-space($handle-id) != ''">
          <datacite:alternateIdentifiers>
            <xsl:choose>
              <xsl:when test="contains($handle-id, 'handle')">
                <datacite:alternateIdentifier alternateIdentifierType="Handle">
                  <xsl:value-of select="$handle-id"/>
                </datacite:alternateIdentifier>
              </xsl:when>
              <xsl:otherwise>
                <datacite:alternateIdentifier alternateIdentifierType="URL">
                  <xsl:value-of select="$handle-id"/>
                </datacite:alternateIdentifier>
              </xsl:otherwise>
            </xsl:choose>
            <xsl:if test="$pkg-id != ''">
              <datacite:alternateIdentifier alternateIdentifierType="PackageID">
                <xsl:value-of select="$pkg-id"/>
              </datacite:alternateIdentifier>
            </xsl:if>
          </datacite:alternateIdentifiers>
        </xsl:if>

        <!-- ── FIX-E: Title with ISO 639-1 xml:lang ───────────────── -->
        <datacite:titles>
          <xsl:variable name="raw-lang" select="normalize-space(./language)"/>
          <datacite:title>
            <xsl:if test="$raw-lang != ''">
              <xsl:attribute name="xml:lang">
                <xsl:call-template name="iso-lang">
                  <xsl:with-param name="lang" select="$raw-lang"/>
                </xsl:call-template>
              </xsl:attribute>
            </xsl:if>
            <xsl:value-of select="normalize-space(./title)"/>
          </datacite:title>
        </datacite:titles>

        <!-- ── FIX-C: Publisher = catalogue owner, NOT creator org ───
             DataCite: "the entity that holds, archives, publishes,
             prints, distributes, releases, issues, or produces the
             resource." For LifeWatch ERIC datasets this is always
             LifeWatch ERIC (via the $default-publisher parameter).
        ─────────────────────────────────────────────────────────────── -->
        <datacite:publisher>
          <xsl:value-of select="$default-publisher"/>
        </datacite:publisher>

        <!-- ── FIX-D: publicationYear with guard ─────────────────── -->
        <xsl:variable name="pub-year"
          select="substring(normalize-space(./pubDate), 1, 4)"/>
        <xsl:if test="string-length($pub-year) = 4">
          <datacite:publicationYear>
            <xsl:value-of select="$pub-year"/>
          </datacite:publicationYear>
        </xsl:if>

        <!-- ── FIX-G: dates — Issued + Collected ─────────────────── -->
        <datacite:dates>
          <xsl:if test="normalize-space(./pubDate) != ''">
            <datacite:date dateType="Issued">
              <xsl:value-of select="normalize-space(./pubDate)"/>
            </datacite:date>
          </xsl:if>
          <!-- singleDateTime temporal coverage -->
          <xsl:for-each select="./coverage/temporalCoverage/singleDateTime">
            <xsl:if test="normalize-space(./calendarDate) != ''">
              <datacite:date dateType="Collected">
                <xsl:value-of select="normalize-space(./calendarDate)"/>
              </datacite:date>
            </xsl:if>
          </xsl:for-each>
          <!-- rangeOfDates → ISO 8601 interval notation -->
          <xsl:for-each select="./coverage/temporalCoverage/rangeOfDates">
            <xsl:variable name="start"
              select="normalize-space(./beginDate/calendarDate)"/>
            <xsl:variable name="end"
              select="normalize-space(./endDate/calendarDate)"/>
            <xsl:if test="$start != '' and $end != ''">
              <datacite:date dateType="Collected">
                <xsl:value-of select="concat($start, '/', $end)"/>
              </datacite:date>
            </xsl:if>
          </xsl:for-each>
        </datacite:dates>

        <!-- Language — ISO 639-1 -->
        <xsl:if test="normalize-space(./language) != ''">
          <dc:language>
            <xsl:call-template name="iso-lang">
              <xsl:with-param name="lang" select="normalize-space(./language)"/>
            </xsl:call-template>
          </dc:language>
        </xsl:if>

        <!-- Description — reads abstract/para correctly -->
        <xsl:if test="normalize-space(./abstract) != ''">
          <datacite:descriptions>
            <datacite:description descriptionType="Abstract">
              <xsl:choose>
                <xsl:when test="./abstract/para">
                  <xsl:for-each select="./abstract/para">
                    <xsl:value-of select="normalize-space(.)"/>
                    <xsl:if test="position() != last()">
                      <xsl:text> </xsl:text>
                    </xsl:if>
                  </xsl:for-each>
                </xsl:when>
                <xsl:otherwise>
                  <xsl:value-of select="normalize-space(./abstract)"/>
                </xsl:otherwise>
              </xsl:choose>
            </datacite:description>
          </datacite:descriptions>
        </xsl:if>

        <!-- ── FIX-H: Sizes ─────────────────────────────────────── -->
        <xsl:if test="./dataTable/physical/size">
          <datacite:sizes>
            <xsl:for-each select="./dataTable/physical/size">
              <xsl:variable name="val"  select="normalize-space(.)"/>
              <xsl:variable name="unit" select="normalize-space(@unit)"/>
              <xsl:if test="$val != ''">
                <datacite:size>
                  <xsl:value-of select="$val"/>
                  <xsl:if test="$unit != ''">
                    <xsl:text> </xsl:text>
                    <xsl:value-of select="$unit"/>
                  </xsl:if>
                </datacite:size>
              </xsl:if>
            </xsl:for-each>
          </datacite:sizes>
        </xsl:if>

        <!-- ── FIX-I: Formats ───────────────────────────────────── -->
        <xsl:variable name="delim"
          select="normalize-space(./dataTable/physical/dataFormat/textFormat/simpleDelimited/fieldDelimiter)"/>
        <xsl:variable name="objname"
          select="translate(normalize-space(./dataTable/physical/objectName), $UC, $LC)"/>
        <xsl:if test="$delim != '' or contains($objname, '.')">
          <datacite:formats>
            <xsl:choose>
              <xsl:when test="contains($objname, '.csv') or $delim = ',' or $delim = ';'">
                <datacite:format>text/csv</datacite:format>
              </xsl:when>
              <xsl:when test="contains($objname, '.tsv') or $delim = '&#9;'">
                <datacite:format>text/tab-separated-values</datacite:format>
              </xsl:when>
              <xsl:when test="contains($objname, '.xml')">
                <datacite:format>application/xml</datacite:format>
              </xsl:when>
              <xsl:when test="contains($objname, '.json')">
                <datacite:format>application/json</datacite:format>
              </xsl:when>
              <xsl:when test="contains($objname, '.xlsx') or contains($objname, '.xls')">
                <datacite:format>application/vnd.openxmlformats-officedocument.spreadsheetml.sheet</datacite:format>
              </xsl:when>
              <xsl:otherwise>
                <datacite:format>text/plain</datacite:format>
              </xsl:otherwise>
            </xsl:choose>
          </datacite:formats>
        </xsl:if>

        <!-- Subjects with optional subjectScheme -->
        <datacite:subjects>
          <xsl:for-each select="./keywordSet">
            <xsl:variable name="thesaurus"
              select="normalize-space(./keywordThesaurus)"/>
            <xsl:for-each select="./keyword">
              <xsl:choose>
                <xsl:when test="$thesaurus != ''
                                and translate($thesaurus, $UC, $LC) != 'none'">
                  <datacite:subject subjectScheme="{$thesaurus}">
                    <xsl:value-of select="normalize-space(.)"/>
                  </datacite:subject>
                </xsl:when>
                <xsl:otherwise>
                  <datacite:subject>
                    <xsl:value-of select="normalize-space(.)"/>
                  </datacite:subject>
                </xsl:otherwise>
              </xsl:choose>
            </xsl:for-each>
          </xsl:for-each>
        </datacite:subjects>

        <!-- ── FIX-J: oaire:file with mimeType + objectType ──────── -->
        <xsl:variable name="file-mime">
          <xsl:choose>
            <xsl:when test="$delim = ';' or $delim = ','
                            or contains($objname, '.csv')">text/csv</xsl:when>
            <xsl:when test="$delim = '&#9;' or contains($objname, '.tsv')">
              text/tab-separated-values</xsl:when>
            <xsl:otherwise>application/octet-stream</xsl:otherwise>
          </xsl:choose>
        </xsl:variable>

        <xsl:for-each select="./distribution/online">
          <xsl:variable name="url" select="normalize-space(./url)"/>
          <xsl:if test="$url != ''">
            <xsl:choose>
              <xsl:when test="contains(translate($url, $UC, $LC), 'doi')">
                <datacite:alternateIdentifiers>
                  <datacite:alternateIdentifier alternateIdentifierType="DOI">
                    <xsl:value-of select="$url"/>
                  </datacite:alternateIdentifier>
                </datacite:alternateIdentifiers>
              </xsl:when>
              <xsl:otherwise>
                <oaire:file mimeType="{$file-mime}" objectType="fulltext">
                  <xsl:value-of select="$url"/>
                </oaire:file>
              </xsl:otherwise>
            </xsl:choose>
          </xsl:if>
        </xsl:for-each>

        <xsl:for-each
          select="../additionalMetadata/metadata/gbif/physical/distribution/online">
          <xsl:variable name="url" select="normalize-space(./url)"/>
          <xsl:if test="$url != ''">
            <xsl:choose>
              <xsl:when test="contains(translate($url, $UC, $LC), 'doi')">
                <datacite:alternateIdentifiers>
                  <datacite:alternateIdentifier alternateIdentifierType="DOI">
                    <xsl:value-of select="$url"/>
                  </datacite:alternateIdentifier>
                </datacite:alternateIdentifiers>
              </xsl:when>
              <xsl:otherwise>
                <oaire:file mimeType="{$file-mime}" objectType="fulltext">
                  <xsl:value-of select="$url"/>
                </oaire:file>
              </xsl:otherwise>
            </xsl:choose>
          </xsl:if>
        </xsl:for-each>

        <!-- ── Creators with nameType, givenName, familyName ──────── -->
        <datacite:creators>
          <xsl:for-each select="./creator">
            <datacite:creator>
              <datacite:creatorName nameType="Personal">
                <xsl:variable name="given"
                  select="normalize-space(./individualName/givenName)"/>
                <xsl:variable name="sur"
                  select="normalize-space(./individualName/surName)"/>
                <xsl:choose>
                  <xsl:when test="$given != '' or $sur != ''">
                    <xsl:value-of select="concat($sur, ', ', $given)"/>
                  </xsl:when>
                  <xsl:otherwise>
                    <xsl:value-of select="normalize-space(./organizationName)"/>
                  </xsl:otherwise>
                </xsl:choose>
              </datacite:creatorName>
              <xsl:if test="normalize-space(./individualName/givenName) != ''">
                <datacite:givenName>
                  <xsl:value-of select="normalize-space(./individualName/givenName)"/>
                </datacite:givenName>
              </xsl:if>
              <xsl:if test="normalize-space(./individualName/surName) != ''">
                <datacite:familyName>
                  <xsl:value-of select="normalize-space(./individualName/surName)"/>
                </datacite:familyName>
              </xsl:if>
              <xsl:if test="normalize-space(./organizationName) != ''">
                <datacite:affiliation>
                  <xsl:value-of select="normalize-space(./organizationName)"/>
                </datacite:affiliation>
              </xsl:if>
              <xsl:if test="normalize-space(./userId) != ''">
                <datacite:nameIdentifier
                    nameIdentifierScheme="ORCID"
                    schemeURI="https://orcid.org">
                  <xsl:value-of select="normalize-space(./userId)"/>
                </datacite:nameIdentifier>
              </xsl:if>
            </datacite:creator>
          </xsl:for-each>
        </datacite:creators>

        <!-- Contributors -->
        <datacite:contributors>
          <xsl:for-each select="./contact">
            <datacite:contributor contributorType="ContactPerson">
              <datacite:contributorName nameType="Personal">
                <xsl:variable name="given"
                  select="normalize-space(./individualName/givenName)"/>
                <xsl:variable name="sur"
                  select="normalize-space(./individualName/surName)"/>
                <xsl:choose>
                  <xsl:when test="$given != '' or $sur != ''">
                    <xsl:value-of select="concat($sur, ', ', $given)"/>
                  </xsl:when>
                  <xsl:otherwise>
                    <xsl:value-of select="normalize-space(./organizationName)"/>
                  </xsl:otherwise>
                </xsl:choose>
              </datacite:contributorName>
              <xsl:if test="normalize-space(./organizationName) != ''">
                <datacite:affiliation>
                  <xsl:value-of select="normalize-space(./organizationName)"/>
                </datacite:affiliation>
              </xsl:if>
              <xsl:if test="normalize-space(./userId) != ''">
                <datacite:nameIdentifier
                    nameIdentifierScheme="ORCID"
                    schemeURI="https://orcid.org">
                  <xsl:value-of select="normalize-space(./userId)"/>
                </datacite:nameIdentifier>
              </xsl:if>
            </datacite:contributor>
          </xsl:for-each>

          <xsl:for-each select="./metadataProvider">
            <datacite:contributor contributorType="DataManager">
              <datacite:contributorName nameType="Personal">
                <xsl:variable name="given"
                  select="normalize-space(./individualName/givenName)"/>
                <xsl:variable name="sur"
                  select="normalize-space(./individualName/surName)"/>
                <xsl:choose>
                  <xsl:when test="$given != '' or $sur != ''">
                    <xsl:value-of select="concat($sur, ', ', $given)"/>
                  </xsl:when>
                  <xsl:otherwise>
                    <xsl:value-of select="normalize-space(./organizationName)"/>
                  </xsl:otherwise>
                </xsl:choose>
              </datacite:contributorName>
              <xsl:if test="normalize-space(./organizationName) != ''">
                <datacite:affiliation>
                  <xsl:value-of select="normalize-space(./organizationName)"/>
                </datacite:affiliation>
              </xsl:if>
              <xsl:if test="normalize-space(./userId) != ''">
                <datacite:nameIdentifier
                    nameIdentifierScheme="ORCID"
                    schemeURI="https://orcid.org">
                  <xsl:value-of select="normalize-space(./userId)"/>
                </datacite:nameIdentifier>
              </xsl:if>
            </datacite:contributor>
          </xsl:for-each>
        </datacite:contributors>

        <!-- ── FIX-K: fundingReferences ───────────────────────── -->
        <xsl:variable name="funding-text">
          <xsl:choose>
            <xsl:when test="normalize-space(./project/funding/para) != ''">
              <xsl:value-of select="normalize-space(./project/funding/para)"/>
            </xsl:when>
            <xsl:otherwise>
              <xsl:value-of select="normalize-space(./project/funding)"/>
            </xsl:otherwise>
          </xsl:choose>
        </xsl:variable>
        <xsl:if test="normalize-space($funding-text) != ''">
          <datacite:fundingReferences>
            <datacite:fundingReference>
              <datacite:funderName>
                <xsl:value-of select="$funding-text"/>
              </datacite:funderName>
            </datacite:fundingReference>
          </datacite:fundingReferences>
        </xsl:if>

        <!-- geoLocations -->
        <xsl:if test="./coverage/geographicCoverage">
          <datacite:geoLocations>
            <xsl:for-each select="./coverage/geographicCoverage">
              <datacite:geoLocation>
                <xsl:if test="normalize-space(./geographicDescription) != ''">
                  <datacite:geoLocationPlace>
                    <xsl:value-of select="normalize-space(./geographicDescription)"/>
                  </datacite:geoLocationPlace>
                </xsl:if>
                <xsl:if test="./boundingCoordinates">
                  <datacite:geoLocationBox>
                    <datacite:westBoundLongitude>
                      <xsl:value-of select="normalize-space(./boundingCoordinates/westBoundingCoordinate)"/>
                    </datacite:westBoundLongitude>
                    <datacite:eastBoundLongitude>
                      <xsl:value-of select="normalize-space(./boundingCoordinates/eastBoundingCoordinate)"/>
                    </datacite:eastBoundLongitude>
                    <datacite:southBoundLatitude>
                      <xsl:value-of select="normalize-space(./boundingCoordinates/southBoundingCoordinate)"/>
                    </datacite:southBoundLatitude>
                    <datacite:northBoundLatitude>
                      <xsl:value-of select="normalize-space(./boundingCoordinates/northBoundingCoordinate)"/>
                    </datacite:northBoundLatitude>
                  </datacite:geoLocationBox>
                </xsl:if>
              </datacite:geoLocation>
            </xsl:for-each>
          </datacite:geoLocations>
        </xsl:if>

        <!-- Resource types -->
        <datacite:resourceType resourceTypeGeneral="Dataset">Dataset</datacite:resourceType>
        <oaire:resourceType
            resourceTypeGeneral="Dataset"
            uri="http://purl.org/coar/resource_type/c_ddb1">dataset</oaire:resourceType>

        <!-- ── FIX-F: rightsList wrapper ──────────────────────── -->
        <xsl:variable name="rights-text">
          <xsl:choose>
            <xsl:when test="normalize-space(./intellectualRights/para) != ''">
              <xsl:value-of select="normalize-space(./intellectualRights/para)"/>
            </xsl:when>
            <xsl:otherwise>
              <xsl:value-of select="normalize-space(./intellectualRights)"/>
            </xsl:otherwise>
          </xsl:choose>
        </xsl:variable>
        <xsl:variable name="rights-lower"
          select="translate($rights-text, $UC, $LC)"/>

        <datacite:rightsList>
          <xsl:choose>
            <xsl:when test="contains($rights-lower, 'creative commons')
                         or contains($rights-lower, 'cc-by')
                         or contains($rights-text,  '4.0')
                         or contains($rights-lower, 'open access')">
              <datacite:rights
                  rightsURI="https://creativecommons.org/licenses/by/4.0/"
                  rightsIdentifier="CC-BY-4.0"
                  rightsIdentifierScheme="SPDX">open access</datacite:rights>
            </xsl:when>
            <xsl:otherwise>
              <datacite:rights
                  rightsURI="http://purl.org/coar/access_right/c_14cb">
                metadata only access
              </datacite:rights>
            </xsl:otherwise>
          </xsl:choose>
        </datacite:rightsList>

      </xsl:for-each>
    </oaire:resource>
  </xsl:template>

</xsl:stylesheet>
