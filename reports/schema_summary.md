# DuckDB Schema Summary

## Overview
- Total Tables: 11
- Total Relationships: 8

## Tables
### classifications
- Primary Key: classificationId
- Column Count: 6
- Referenced by:
  - instances (via classificationId)

### datasets
- Primary Key: datasetId
- Column Count: 6
- Referenced by:
  - instances (via datasetId)

### encryption
- Primary Key: encryptionId
- Column Count: 7
- Referenced by:
  - instances (via encryptionId)

### instances
- Primary Key: instanceId
- Column Count: 32

### messages
- Primary Key: messageId
- Column Count: 4

### objects
- Primary Key: objectId
- Column Count: 16
- Referenced by:
  - instances (via objectId)

### osPermissions
- Primary Key: permissionId
- Column Count: 5
- Referenced by:
  - objects (via permissionId)

### osSecurity
- Primary Key: securityId
- Column Count: 9

### parentPaths
- Primary Key: parentId
- Column Count: 3
- Referenced by:
  - objects (via parentId)

### services
- Primary Key: serviceId
- Column Count: 14
- Referenced by:
  - instances (via serviceId)

### tagSets
- Primary Key: tagSetId
- Column Count: 2
- Referenced by:
  - instances (via tagSetId)
