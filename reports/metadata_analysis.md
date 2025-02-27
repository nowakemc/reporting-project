# File Metadata Analysis Report

## Summary

- **File Types Analyzed**: 19
- **Total Unique Metadata Fields**: 394
- **Common Fields** (across 50%+ of file types): 4
- **Unique Fields**: 291

## Common Metadata Fields

These fields appear in multiple file types:

| Field | % of File Types | Example Values |
|-------|----------------|----------------|
| `X-TIKA:Parsed-By-Full-Set` | 100.0% | org.apache.tika.parser.CompositeParser; org.apache.tika.parser.DefaultParser; org.apache.tika.parser.csv.TextAndCSVParser, com.aparavi.tika_api.parsers.email.CustomRFC822Parser |
| `Content-Type` | 100.0% | text/plain; charset=windows-1252, message/rfc822, text/plain; charset=ISO-8859-1, ... |
| `dcterms:created` | 52.6% | 1993-04-26T21:11:05Z |
| `dc:creator` | 52.6% | Nestlé S.A., Help Desk, Tom Breedlove, ... |

## File Type Analysis

### TXT Files

- **Total Files**: 9975
- **Analyzed**: 500 samples
- **Unique Metadata Fields**: 4

#### Top Metadata Fields

| Field | Frequency | Example Values |
|-------|-----------|----------------|
| `Content-Type` | 100.0% | text/plain; charset=windows-1252, message/rfc822, text/plain; charset=ISO-8859-1, ... |
| `X-TIKA:Parsed-By-Full-Set` | 100.0% | org.apache.tika.parser.CompositeParser; org.apache.tika.parser.DefaultParser; org.apache.tika.parser.csv.TextAndCSVParser, com.aparavi.tika_api.parsers.email.CustomRFC822Parser |
| `Content-Encoding` | 78.8% | windows-1252, ISO-8859-1 |
| `dcterms:created` | 0.6% | 1993-04-26T21:11:05Z |

### PDF Files

- **Total Files**: 1416
- **Analyzed**: 500 samples
- **Unique Metadata Fields**: 157

#### Top Metadata Fields

| Field | Frequency | Example Values |
|-------|-----------|----------------|
| `xmpTPg:NPages` | 100.0% | 148, 11, 10, ... |
| `Content-Type` | 100.0% | application/pdf, application/illustrator |
| `pdf:containsNonEmbeddedFont` | 100.0% | false, true |
| `access_permission:modify_annotations` | 100.0% | false, true |
| `pdf:hasXMP` | 100.0% | true, false |
| `pdf:hasCollection` | 100.0% | false |
| `access_permission:fill_in_form` | 100.0% | false, true |
| `access_permission:assemble_document` | 100.0% | false, true |
| `access_permission:can_print` | 100.0% | true |
| `pdf:num3DAnnotations` | 100.0% | 0 |

#### Fields Unique to this File Type

| Field | Example Values |
|-------|----------------|
| `AFTY_WORDLINK` |  |
| `APTKVER` | 5.5.1.15339 Pro Production-64 |
| `Build` |  |
| `CUS_DocIDOperation` | EVERY PAGE |
| `CUS_DocIDString` | 45155.0043.8617954.1 |
| `CUS_DocIDbChkLibDB` | 0 |
| `CUS_DocIDbchkAuthorName` | 0 |
| `CUS_DocIDbchkClientNumber` | -1 |
| `CUS_DocIDbchkDate` | 0 |
| `CUS_DocIDbchkDocbLocation` | 0 |

*Plus 100 more unique fields*

### EML Files

- **Total Files**: 425
- **Analyzed**: 425 samples
- **Unique Metadata Fields**: 13

#### Top Metadata Fields

| Field | Frequency | Example Values |
|-------|-----------|----------------|
| `Message-To` | 100.0% | Zak Carpenter <zak@nowakelabs.com>, Max Carpenter <max@nowakelabs.com>; Matt Carpenter <matt@nowakelabs.com>, Zak Carpenter <zak@nowakelabs.com>; Max Carpenter <max@nowakelabs.com>, ... |
| `dcterms:created` | 100.0% | 2024-11-01T15:42:53Z, 2024-10-31T19:28:50Z, 2024-11-04T17:19:47Z, ... |
| `Content-Type` | 100.0% | message/rfc822 |
| `X-TIKA:Parsed-By-Full-Set` | 100.0% | com.aparavi.tika_api.parsers.email.CustomRFC822Parser |
| `dc:title` | 99.8% | BI Tools, RE: Westerville Activities, Multiple Test 2, ... |
| `dc:subject` | 99.8% | BI Tools, RE: Westerville Activities, Multiple Test 2, ... |
| `dc:creator` | 99.5% | Matt Carpenter <matt@nowakelabs.com>, Zak Carpenter <zak@nowakelabs.com>, Max Carpenter <max@nowakelabs.com>, ... |
| `Message-From` | 99.5% | Matt Carpenter <matt@nowakelabs.com>, Zak Carpenter <zak@nowakelabs.com>, Max Carpenter <max@nowakelabs.com>, ... |
| `Message:From-Email` | 99.5% | matt@nowakelabs.com, zak@nowakelabs.com, max@nowakelabs.com, ... |
| `Message:From-Name` | 99.1% | Matt Carpenter, Zak Carpenter, Max Carpenter, ... |

#### Fields Unique to this File Type

| Field | Example Values |
|-------|----------------|
| `Message-Cc` | Max Carpenter <max@nowakelabs.com> |
| `Message-From` | Matt Carpenter <matt@nowakelabs.com>, Zak Carpenter <zak@nowakelabs.com>, Max Carpenter <max@nowakelabs.com>, ... |
| `Message-To` | Zak Carpenter <zak@nowakelabs.com>, Max Carpenter <max@nowakelabs.com>; Matt Carpenter <matt@nowakelabs.com>, Zak Carpenter <zak@nowakelabs.com>; Max Carpenter <max@nowakelabs.com>, ... |
| `Message:From-Email` | matt@nowakelabs.com, zak@nowakelabs.com, max@nowakelabs.com, ... |
| `Message:From-Name` | Matt Carpenter, Zak Carpenter, Max Carpenter, ... |
| `Multipart-Boundary` | _000_SJ0PR07MB7757F05B8C858143A20105E1BC562SJ0PR07MB7757namp_, _000_SJ0PR07MB7757098B8EF1E99B5BF1EF65BC512SJ0PR07MB7757namp_, _000_BLAPR07MB7746BC34B86078AC9BC4B300BC552BLAPR07MB7746namp_, ... |
| `Multipart-Subtype` | alternative, mixed |

### JS Files

- **Total Files**: 333
- **Analyzed**: 333 samples
- **Unique Metadata Fields**: 3

#### Top Metadata Fields

| Field | Frequency | Example Values |
|-------|-----------|----------------|
| `Content-Encoding` | 100.0% | UTF-8, windows-1252 |
| `Content-Type` | 100.0% | application/javascript; charset=UTF-8, application/javascript; charset=windows-1252 |
| `X-TIKA:Parsed-By-Full-Set` | 100.0% | org.apache.tika.parser.CompositeParser; org.apache.tika.parser.DefaultParser; org.apache.tika.parser.csv.TextAndCSVParser |

### DOCX Files

- **Total Files**: 135
- **Analyzed**: 135 samples
- **Unique Metadata Fields**: 94

#### Top Metadata Fields

| Field | Frequency | Example Values |
|-------|-----------|----------------|
| `Content-Type` | 100.0% | application/vnd.openxmlformats-officedocument.wordprocessingml.document |
| `X-TIKA:Parsed-By-Full-Set` | 100.0% | org.apache.tika.parser.CompositeParser; org.apache.tika.parser.microsoft.ooxml.OOXMLParser |
| `dcterms:created` | 89.6% | 2020-11-12T08:07:32Z, 2007-03-28T20:58:00Z, 2020-11-12T07:57:20Z, ... |
| `dcterms:modified` | 89.6% | 2020-11-12T08:07:32Z, 2007-03-28T20:58:00Z, 2020-11-12T07:57:20Z, ... |
| `dc:creator` | 78.5% | MB, Stacey Rivera, slhudson, ... |
| `cp:revision` | 71.9% | 2, 5, 3, ... |
| `xmpTPg:NPages` | 71.1% | 5, 1, 18, ... |
| `dc:modifier` | 68.1% | dalbert, MB, Stacey Rivera, ... |
| `dc:publisher` | 51.1% | Central New Mexico Community College, Georgia Dept of Human Services, bewglobal, ... |
| `dc:title` | 48.9% | CONTRACT OF PROBATIONARY EMPLOYMENT, Daily Progress Notes (The “SOAP” note), Microsoft Word - 33203935.docx, ... |

#### Fields Unique to this File Type

| Field | Example Values |
|-------|----------------|
| `custom:Author0` | Karen |
| `custom:AuthorName` | Brp |
| `custom:BusinessServices` | 734;#Talent Acquisition Support|426a5316-1625-4db5-8930-ba53186cc339 |
| `custom:CUS_DocIDOperation` | EVERY PAGE |
| `custom:CUS_DocIDString` | B4190829.2 |
| `custom:CUS_DocIDbChkLibDB` | -1 |
| `custom:CUS_DocIDbchkAuthorName` | 0 |
| `custom:CUS_DocIDbchkClientNumber` | 0 |
| `custom:CUS_DocIDbchkDate` | 0 |
| `custom:CUS_DocIDbchkDocumentName` | 0 |

*Plus 63 more unique fields*

### SPCOLOR Files

- **Total Files**: 96
- **Analyzed**: 96 samples
- **Unique Metadata Fields**: 2

#### Top Metadata Fields

| Field | Frequency | Example Values |
|-------|-----------|----------------|
| `Content-Type` | 100.0% | application/xml |
| `X-TIKA:Parsed-By-Full-Set` | 100.0% | org.apache.tika.parser.CompositeParser; org.apache.tika.parser.DefaultParser; org.apache.tika.parser.xml.DcXMLParser |

### DOC Files

- **Total Files**: 47
- **Analyzed**: 47 samples
- **Unique Metadata Fields**: 32

#### Top Metadata Fields

| Field | Frequency | Example Values |
|-------|-----------|----------------|
| `dcterms:created` | 100.0% | 2013-03-27T14:42:00Z, 2011-03-11T23:02:00Z, 2015-07-10T04:31:00Z, ... |
| `xmpTPg:NPages` | 100.0% | 1, 76, 10, ... |
| `Content-Type` | 100.0% | application/msword, application/vnd.openxmlformats-officedocument.wordprocessingml.document |
| `cp:revision` | 100.0% | 10, 2, 3, ... |
| `X-TIKA:Parsed-By-Full-Set` | 100.0% | org.apache.tika.parser.CompositeParser; org.apache.tika.parser.microsoft.OfficeParser, org.apache.tika.parser.CompositeParser; org.apache.tika.parser.microsoft.ooxml.OOXMLParser |
| `dcterms:modified` | 100.0% | 2013-12-05T16:47:00Z, 2011-03-11T23:02:00Z, 2015-07-10T04:31:00Z, ... |
| `dc:creator` | 97.9% | Jenn, CoP, Chris Borthwick, ... |
| `dc:modifier` | 97.9% | Jason Leppert, mj4749, Georgia Wilton, ... |
| `dc:title` | 83.0% | Employee Compensation Plan For The Windsor Group LLC, Information Security Policy Template v1.0, CONTRACT OF EMPLOYMENT, ... |
| `X-TIKA:origResourceName` | 12.8% | C:\WINNT40\Profiles\mathildb\Application Data\Microsoft\Word\AutoRecovery save of 2002 dom.asd; F:\MSWORD\2002 dom.doc; F:\MSWORD\2002 dom.doc; C:\WINNT40\Profiles\mathildb\Application Data\Microsoft\Word\AutoRecovery save of 2002 dom.asd; C:\WINNT40\Profiles\mathildb\Application Data\Microsoft\Word\AutoRecovery save of 2002 dom.asd; C:\WINNT40\Profiles\mathildb\Application Data\Microsoft\Word\AutoRecovery save of 2002 dom.asd; F:\MSWORD\2002 dom.doc; C:\WINNT40\Profiles\mathildb\Application Data\Microsoft\Word\AutoRecovery save of 2002 dom.asd; C:\WINNT40\Profiles\mathildb\Application Data\Microsoft\Word\AutoRecovery save of 2002 dom.asd; C:\website\dom worker contract Eng.doc, A:\INDEMNITY AGREEMENT Form 16.doc; A:\INDEMNITY AGREEMENT.doc; A:\INDEMNITY AGREEMENT.doc, I:\Inetpub\wwwroot\interweb\docs\legislation\bcea\CONTRACT OF EMPLOYMENT.doc; C:\WINDOWS\TEMP\mso32A.TMP, ... |

#### Fields Unique to this File Type

| Field | Example Values |
|-------|----------------|
| `X-TIKA:origResourceName` | C:\WINNT40\Profiles\mathildb\Application Data\Microsoft\Word\AutoRecovery save of 2002 dom.asd; F:\MSWORD\2002 dom.doc; F:\MSWORD\2002 dom.doc; C:\WINNT40\Profiles\mathildb\Application Data\Microsoft\Word\AutoRecovery save of 2002 dom.asd; C:\WINNT40\Profiles\mathildb\Application Data\Microsoft\Word\AutoRecovery save of 2002 dom.asd; C:\WINNT40\Profiles\mathildb\Application Data\Microsoft\Word\AutoRecovery save of 2002 dom.asd; F:\MSWORD\2002 dom.doc; C:\WINNT40\Profiles\mathildb\Application Data\Microsoft\Word\AutoRecovery save of 2002 dom.asd; C:\WINNT40\Profiles\mathildb\Application Data\Microsoft\Word\AutoRecovery save of 2002 dom.asd; C:\website\dom worker contract Eng.doc, A:\INDEMNITY AGREEMENT Form 16.doc; A:\INDEMNITY AGREEMENT.doc; A:\INDEMNITY AGREEMENT.doc, I:\Inetpub\wwwroot\interweb\docs\legislation\bcea\CONTRACT OF EMPLOYMENT.doc; C:\WINDOWS\TEMP\mso32A.TMP, ... |
| `custom:Date` | 2012-02-22T00:00:00Z |
| `custom:Linked To Page` | 106;#hr.aspx |
| `custom:Record Type` | 5 |
| `custom:Security` | 1 |
| `custom:UN Language` | 1 |
| `custom:_AdHocReviewCycleID` | -694349277, -903623363 |
| `custom:_Author` | skelly |
| `custom:_AuthorEmail` | ed.armitage@emsa.ca.gov, ac6543@wayne.edu |
| `custom:_AuthorEmailDisplayName` | Ed Armitage, Alicia Pendleton |

*Plus 4 more unique fields*

### XML Files

- **Total Files**: 39
- **Analyzed**: 39 samples
- **Unique Metadata Fields**: 9

#### Top Metadata Fields

| Field | Frequency | Example Values |
|-------|-----------|----------------|
| `Content-Type` | 100.0% | application/xml, application/vnd.ms-wordml, application/vnd.ms-word2006ml |
| `X-TIKA:Parsed-By-Full-Set` | 100.0% | org.apache.tika.parser.CompositeParser; org.apache.tika.parser.DefaultParser; org.apache.tika.parser.xml.DcXMLParser, org.apache.tika.parser.CompositeParser; org.apache.tika.parser.DefaultParser; org.apache.tika.parser.microsoft.xml.WordMLParser, org.apache.tika.parser.CompositeParser; org.apache.tika.parser.DefaultParser; org.apache.tika.parser.microsoft.ooxml.xwpf.ml2006.Word2006MLParser |
| `dc:creator` | 5.1% | Michelle Duran Dollar General Corporation |
| `dcterms:created` | 5.1% | 2015-06-11T00:00:00Z, 2020-11-11T22:49:00Z |
| `cp:revision` | 5.1% | 2 |
| `dc:title` | 5.1% | SSC Employee Handbook 20080916 draft |
| `dc:modifier` | 5.1% | Joe Maionchi |
| `cp:version` | 2.6% | 16 |
| `dcterms:modified` | 2.6% | 2020-11-11T22:49:00Z |

### XLSX Files

- **Total Files**: 37
- **Analyzed**: 37 samples
- **Unique Metadata Fields**: 55

#### Top Metadata Fields

| Field | Frequency | Example Values |
|-------|-----------|----------------|
| `X-TIKA:Parsed-By-Full-Set` | 100.0% | class com.aparavi.tika_api.parsers.excel.ExcelParser |
| `protected` | 100.0% | false |
| `Version` | 81.1% | 16.0300, 14.0300, 1.0.2, ... |
| `dcterms:created` | 81.1% | 2006-09-16T00:00:00, 2008-12-10T22:55:38, 2001-02-14T05:31:45, ... |
| `Content-Type` | 81.1% | application/vnd.openxmlformats-officedocument.spreadsheetml.sheet |
| `dcterms:modified` | 81.1% | 2019-04-30T18:25:23, 2020-02-21T14:07:28, 2014-01-08T20:07:55, ... |
| `Security` | 78.4% | 0 |
| `SharedDoc` | 78.4% | false |
| `HyperlinksChanged` | 78.4% | false |
| `LinksUpToDate` | 78.4% | false |

#### Fields Unique to this File Type

| Field | Example Values |
|-------|----------------|
| `ChapterId` | 20987 |
| `ChapterName` | Consol. Income Statements |
| `Classification` | UNCLASSIFIED NONE Emma Cameron |
| `Copyright` | 2015 Vertex42 LLC, Vertex42 LLC |
| `DSDBI ClassificationCLASSIFICATION` | UNCLASSIFIED |
| `DSDBI ClassificationDLM FOR SEC-MARKINGS` | NONE |
| `DocumentNo` | a727e605-2268-45d3-b452-6211d663cb08 |
| `MSIP_Label_2b30ed1b-e95f-40b5-af89-828263f287a7_ActionId` | ad9a0d16-5e10-4407-9815-68da72d00bf6 |
| `MSIP_Label_2b30ed1b-e95f-40b5-af89-828263f287a7_Application` | Microsoft Azure Information Protection |
| `MSIP_Label_2b30ed1b-e95f-40b5-af89-828263f287a7_Enabled` | True |

*Plus 17 more unique fields*

### WEBPART Files

- **Total Files**: 30
- **Analyzed**: 30 samples
- **Unique Metadata Fields**: 2

#### Top Metadata Fields

| Field | Frequency | Example Values |
|-------|-----------|----------------|
| `Content-Type` | 100.0% | application/xml |
| `X-TIKA:Parsed-By-Full-Set` | 100.0% | org.apache.tika.parser.CompositeParser; org.apache.tika.parser.DefaultParser; org.apache.tika.parser.xml.DcXMLParser |

### PPTX Files

- **Total Files**: 26
- **Analyzed**: 26 samples
- **Unique Metadata Fields**: 15

#### Top Metadata Fields

| Field | Frequency | Example Values |
|-------|-----------|----------------|
| `dcterms:created` | 100.0% | 2020-11-12T19:25:15Z, 2020-11-12T19:46:40Z, 2020-11-11T21:53:44Z, ... |
| `Content-Type` | 100.0% | application/vnd.openxmlformats-officedocument.presentationml.presentation |
| `X-TIKA:Parsed-By-Full-Set` | 100.0% | org.apache.tika.parser.CompositeParser; org.apache.tika.parser.microsoft.ooxml.OOXMLParser |
| `dcterms:modified` | 100.0% | 2020-11-12T19:25:15Z, 2020-11-12T19:46:40Z, 2020-11-11T21:53:44Z, ... |
| `custom:LastSaved` | 96.2% | 2020-11-12T00:00:00Z, 2020-11-11T00:00:00Z, 2020-11-20T00:00:00Z, ... |
| `custom:Creator` | 92.3% | Adobe InDesign CC 2017 (Macintosh), Adobe InDesign CC 14.0 (Macintosh), Adobe InDesign CS6 (Macintosh), ... |
| `custom:Created` | 92.3% | 2018-01-24T00:00:00Z, 2019-11-18T00:00:00Z, 2013-11-04T00:00:00Z, ... |
| `dc:creator` | 46.2% | Jason Calacanis, Sabrina.Schmidt, Erica Paul, ... |
| `dc:title` | 42.3% | coca-cola-code-of-conduct, BUSINESS CONDUCT GUIDELINES TRUST COMES FIRST, Microsoft Word - Employee_Referral_Form, ... |
| `custom:TemplateCategory` | 3.8% | 56;#PowerPoint|38594cf2-1e08-47ec-85aa-6ac80b7ffd1b |

#### Fields Unique to this File Type

| Field | Example Values |
|-------|----------------|
| `custom:Division` | 2;#Corporate|2b75fef5-1ea9-4623-9446-16bf4a18895c |
| `custom:TemplateCategory` | 56;#PowerPoint|38594cf2-1e08-47ec-85aa-6ac80b7ffd1b |

### HTM Files

- **Total Files**: 25
- **Analyzed**: 25 samples
- **Unique Metadata Fields**: 80

#### Top Metadata Fields

| Field | Frequency | Example Values |
|-------|-----------|----------------|
| `Content-Type` | 100.0% | text/html; charset=UTF-8, text/html; charset=windows-1252, text/html; charset=ISO-8859-1, ... |
| `Content-Encoding` | 100.0% | UTF-8, windows-1252, ISO-8859-1 |
| `dc:title` | 100.0% | Privacy Statement | Accenture, SpringCM® MASTER SUBSCRIPTION AND SERVICES AGREEMENT, Terms of use | Lumin PDF, ... |
| `X-TIKA:Parsed-By-Full-Set` | 100.0% | org.apache.tika.parser.CompositeParser; org.apache.tika.parser.DefaultParser; org.apache.tika.parser.html.HtmlParser |
| `Content-Language` | 84.0% | en, en-US |
| `viewport` | 80.0% | width=device-width,initial-scale=1, width=device-width, initial-scale=1, width=device-width, initial-scale=1, shrink-to-fit=no, ... |
| `dc:description` | 64.0% | Learn how Accenture protects your personal data and know your rights in relation to your personal data. Read more about our Privacy Statement., SpringCM Terms of Service, Read carefully all the provisions of our tems of use. Edit your PDF documents with Lumin PDF editor., ... |
| `og:title` | 60.0% | Privacy Statement | Accenture, SpringCM® MASTER SUBSCRIPTION AND SERVICES AGREEMENT, Terms of use | Lumin PDF, ... |
| `og:description` | 56.0% | Learn how Accenture protects your personal data and know your rights in relation to your personal data. Read more about our Privacy Statement., SpringCM Terms of Service, Read carefully all the provisions of our tems of use. Edit your PDF documents with Lumin PDF editor., ... |
| `Content-Type-Hint` | 48.0% | text/html; charset=utf-8, text/html; charset=iso-8859-1, text/html; charset=UTF-8 |

#### Fields Unique to this File Type

| Field | Example Values |
|-------|----------------|
| `AUTHOR` | Michael C Volker |
| `CmsPageId` | 247 |
| `Content-Location` | https://www.hr.uillinois.edu/cms/One.aspx?portalId=4292&pageId=5639 |
| `Description` | Oracle Corporation and our subsidiaries and affiliates (, A sample shareholders agreement, This EULA is a legally binding agreement setting forth the terms and conditions governing the use and operation of Veeam’s products and its documentation. |
| `Generator` | Drupal 8 (https://www.drupal.org) |
| `HandheldFriendly` | true |
| `KeyWords` | Shareholders Agreement, Business Basics, High Tech, Volker |
| `Language` | en |
| `MobileOptimized` | width |
| `ROBOTS` | FOLLOW,INDEX |

*Plus 34 more unique fields*

### SPFONT Files

- **Total Files**: 24
- **Analyzed**: 24 samples
- **Unique Metadata Fields**: 2

#### Top Metadata Fields

| Field | Frequency | Example Values |
|-------|-----------|----------------|
| `Content-Type` | 100.0% | application/xml |
| `X-TIKA:Parsed-By-Full-Set` | 100.0% | org.apache.tika.parser.CompositeParser; org.apache.tika.parser.DefaultParser; org.apache.tika.parser.xml.DcXMLParser |

### DWP Files

- **Total Files**: 23
- **Analyzed**: 23 samples
- **Unique Metadata Fields**: 2

#### Top Metadata Fields

| Field | Frequency | Example Values |
|-------|-----------|----------------|
| `Content-Type` | 100.0% | application/xml |
| `X-TIKA:Parsed-By-Full-Set` | 100.0% | org.apache.tika.parser.CompositeParser; org.apache.tika.parser.DefaultParser; org.apache.tika.parser.xml.DcXMLParser |

### XLS Files

- **Total Files**: 17
- **Analyzed**: 17 samples
- **Unique Metadata Fields**: 35

#### Top Metadata Fields

| Field | Frequency | Example Values |
|-------|-----------|----------------|
| `Security` | 100.0% | 0 |
| `Version` | 100.0% | 12.0000, 15.0000, 11.9999, ... |
| `dcterms:created` | 100.0% | 2009-09-28T19:19:09, 2008-02-25T15:24:37, 1997-01-31T19:43:21, ... |
| `SharedDoc` | 100.0% | false |
| `HyperlinksChanged` | 100.0% | false |
| `Content-Type` | 100.0% | application/vnd.ms-excel |
| `X-TIKA:Parsed-By-Full-Set` | 100.0% | class com.aparavi.tika_api.parsers.excel.ExcelParser |
| `LinksUpToDate` | 100.0% | false |
| `dcterms:modified` | 100.0% | 2010-01-06T00:23:38, 2017-12-28T15:33:11, 2009-02-18T00:29:19, ... |
| `protected` | 100.0% | false |

#### Fields Unique to this File Type

| Field | Example Values |
|-------|----------------|
| `_PID_HLINKS` | [B@7d4ce5d8, [B@148c0ba0, [B@4845dc79, ... |
| `_PreviousAdHocReviewCycleID` | 1986414594, -1858072196 |
| `containVBA` | true |
| `formulasLongerThan100` | true |

### MASTER Files

- **Total Files**: 12
- **Analyzed**: 12 samples
- **Unique Metadata Fields**: 9

#### Top Metadata Fields

| Field | Frequency | Example Values |
|-------|-----------|----------------|
| `Content-Encoding` | 100.0% | UTF-8 |
| `Content-Type` | 100.0% | text/plain; charset=UTF-8, text/html; charset=UTF-8 |
| `X-TIKA:Parsed-By-Full-Set` | 100.0% | org.apache.tika.parser.CompositeParser; org.apache.tika.parser.DefaultParser; org.apache.tika.parser.csv.TextAndCSVParser, org.apache.tika.parser.CompositeParser; org.apache.tika.parser.DefaultParser; org.apache.tika.parser.html.HtmlParser |
| `Content-Type-Hint` | 50.0% | text/html; charset=utf-8 |
| `Content-Language` | 50.0% | <%$Resources:wss,language_value%> |
| `GENERATOR` | 50.0% | Microsoft SharePoint |
| `Expires` | 50.0% | 0 |
| `progid` | 50.0% | SharePoint.WebPartPage.Document |
| `X-UA-Compatible` | 25.0% | IE=8 |

#### Fields Unique to this File Type

| Field | Example Values |
|-------|----------------|
| `Expires` | 0 |
| `progid` | SharePoint.WebPartPage.Document |

### HTML Files

- **Total Files**: 7
- **Analyzed**: 7 samples
- **Unique Metadata Fields**: 39

#### Top Metadata Fields

| Field | Frequency | Example Values |
|-------|-----------|----------------|
| `Content-Type` | 100.0% | text/html; charset=UTF-8, text/html; charset=ISO-8859-1 |
| `Content-Encoding` | 100.0% | UTF-8, ISO-8859-1 |
| `dc:title` | 100.0% | Master Services Agreement | Validity Inc., Mission, Vision and Core Values - capradio.org, Privacy Policy - About Us - pdfforge.org, ... |
| `X-TIKA:Parsed-By-Full-Set` | 100.0% | org.apache.tika.parser.CompositeParser; org.apache.tika.parser.DefaultParser; org.apache.tika.parser.html.HtmlParser |
| `viewport` | 85.7% | width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=0, width=device-width, initial-scale=1, minimum-scale=1, width=device-width, initial-scale=1, ... |
| `og:title` | 71.4% | Master Services Agreement | Validity Inc., Mission, Vision and Core Values, Privacy Policy, ... |
| `og:url` | 71.4% | https://www.validity.com/masterservicesagreement/, https://www.capradio.org/2007, https://www.pdfforge.org/about-us/privacy-policy, ... |
| `Content-Language` | 71.4% | en-US, en |
| `og:locale` | 57.1% | en_US, en |
| `og:site_name` | 57.1% | Validity, Create, edit and merge PDFs easily - pdfforge, amazon.jobs |

#### Fields Unique to this File Type

| Field | Example Values |
|-------|----------------|
| `bingbot` | index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1 |
| `csrf-param` | authenticity_token |
| `csrf-token` | N3YT273kkbdkdgxEbD96dfRyeUApJuAQEx0vUrS0MJj2VNqNBOeuTkEQThjY7L+zqSk9iXeyfjt5qi3k+G9Lgg== |
| `googlebot` | index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1 |
| `has_audio` | 0 |
| `nid` | 2007 |
| `programs` | none |

### PREVIEW Files

- **Total Files**: 6
- **Analyzed**: 6 samples
- **Unique Metadata Fields**: 3

#### Top Metadata Fields

| Field | Frequency | Example Values |
|-------|-----------|----------------|
| `Content-Encoding` | 100.0% | windows-1252 |
| `Content-Type` | 100.0% | text/plain; charset=windows-1252 |
| `X-TIKA:Parsed-By-Full-Set` | 100.0% | org.apache.tika.parser.CompositeParser; org.apache.tika.parser.DefaultParser; org.apache.tika.parser.csv.TextAndCSVParser |

### PDF Files

- **Total Files**: 6
- **Analyzed**: 6 samples
- **Unique Metadata Fields**: 38

#### Top Metadata Fields

| Field | Frequency | Example Values |
|-------|-----------|----------------|
| `xmpTPg:NPages` | 100.0% | 15, 6, 4, ... |
| `Content-Type` | 100.0% | application/pdf |
| `pdf:containsNonEmbeddedFont` | 100.0% | false, true |
| `access_permission:modify_annotations` | 100.0% | true |
| `pdf:hasXMP` | 100.0% | true, false |
| `pdf:hasCollection` | 100.0% | false |
| `access_permission:fill_in_form` | 100.0% | true |
| `access_permission:assemble_document` | 100.0% | true |
| `dcterms:created` | 100.0% | 2017-10-18T19:05:38Z, 2016-11-28T22:14:54Z, 2016-01-04T16:35:54Z, ... |
| `access_permission:can_print` | 100.0% | true |

#### Fields Unique to this File Type

| Field | Example Values |
|-------|----------------|
| `_DocHome` | -526115632 |

