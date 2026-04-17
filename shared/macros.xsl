<?xml version="1.0" encoding="UTF-8"?>
<!--
  shared/macros.xsl
  ==================
  Common named templates shared across LifeWatch XSLT transformations.

  Import this file with:
    <xsl:import href="../../shared/macros.xsl"/>

  Templates provided:
    - replace-string   : recursive string substitution (XSLT 1.0)
    - get-full-path    : slash-delimited path from root to current element
    - normalize-date   : converts YYYY → YYYY-01-01, passes YYYY-MM-DD through
    - is-empty-string  : returns 'true' if a string is empty or whitespace-only
-->
<xsl:stylesheet
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  version="1.0">

  <!-- ================================================================
       replace-string
       Recursively replaces all occurrences of $replace with $with
       inside $text.
       ================================================================ -->
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

  <!-- ================================================================
       get-full-path
       Emits the XPath from the document root to the context node.
       Usage: <xsl:apply-templates select="." mode="get-full-path"/>
       ================================================================ -->
  <xsl:template match="node()" mode="get-full-path">
    <xsl:for-each select="ancestor-or-self::*">
      <xsl:text>/</xsl:text>
      <xsl:value-of select="name()"/>
    </xsl:for-each>
  </xsl:template>

  <!-- ================================================================
       normalize-date
       Converts a year-only value (YYYY) to YYYY-01-01.
       Passes through any value already containing a hyphen.
       ================================================================ -->
  <xsl:template name="normalize-date">
    <xsl:param name="date"/>
    <xsl:choose>
      <xsl:when test="contains($date, '-')">
        <xsl:value-of select="$date"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="$date"/>
        <xsl:text>-01-01</xsl:text>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <!-- ================================================================
       is-empty-string
       Returns the string 'true' if $value is empty or contains only
       whitespace; 'false' otherwise.
       ================================================================ -->
  <xsl:template name="is-empty-string">
    <xsl:param name="value"/>
    <xsl:choose>
      <xsl:when test="normalize-space($value) = ''">
        <xsl:text>true</xsl:text>
      </xsl:when>
      <xsl:otherwise>
        <xsl:text>false</xsl:text>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

</xsl:stylesheet>
