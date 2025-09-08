# Vogue Manager Test Scenarios

This document outlines comprehensive test scenarios to validate that Vogue Manager works like real Prism pipeline management software.

## 1. Project Management Tests

### 1.1 Project Creation
**Test Case**: Create a new project with custom settings
- **Steps**:
  1. Launch Vogue Manager
  2. Click "New Project" button
  3. Fill in project details:
     - Name: "TestProject_001"
     - Path: Select a test directory
     - Description: "Test project for validation"
     - FPS: 30
     - Resolution: 4K (3840x2160)
  4. Add custom departments:
     - Click "Add Department" → Add "Modeling" with color #FF6B6B
     - Click "Add Department" → Add "Texturing" with color #4ECDC4
     - Click "Add Department" → Add "Rigging" with color #45B7D1
  5. Remove default department (select and click "Remove Department")
  6. Click "OK" to create project
- **Expected Result**: 
  - Project directory structure created
  - pipeline.json file generated with correct settings
  - Project loads automatically in Vogue Manager
  - Log shows "Created new project: TestProject_001"

### 1.2 Project Loading
**Test Case**: Load existing project
- **Steps**:
  1. Click "Load Project" button
  2. Navigate to test project directory
  3. Select project folder
  4. Click "Open"
- **Expected Result**:
  - Project loads successfully
  - All project settings displayed correctly
  - Asset and shot lists populated
  - Log shows "Loaded project: [ProjectName]"

### 1.3 Project Validation
**Test Case**: Validate project integrity
- **Steps**:
  1. Load a test project
  2. Go to Tools → Validate Project
  3. Review validation results
- **Expected Result**:
  - All project files validated
  - No critical errors reported
  - Log shows validation completion status

## 2. Asset Management Tests

### 2.1 Asset Creation
**Test Case**: Create assets in different categories
- **Steps**:
  1. Load test project
  2. Right-click on "Characters" → "Create Asset"
  3. Fill asset details:
     - Name: "Hero_Character"
     - Description: "Main character for the project"
     - Department: "Modeling"
  4. Click "Create"
  5. Repeat for "Environments" → "Forest_Environment"
  6. Repeat for "Props" → "Magic_Sword"
- **Expected Result**:
  - Asset directories created in correct locations
  - Assets appear in asset list
  - Log shows "Created asset: [AssetName]"

### 2.2 Asset Versioning
**Test Case**: Create and manage asset versions
- **Steps**:
  1. Select an asset from the list
  2. Click "Create Version" button
  3. Select file to publish (create dummy .ma/.mb file)
  4. Add version comment: "Initial model"
  5. Click "Publish"
  6. Create second version with different file
  7. Add comment: "Updated topology"
  8. Click "Publish"
- **Expected Result**:
  - Versions created with incremental numbering (v001, v002)
  - Version comments saved
  - Files copied to correct version directories
  - Log shows "Published version v[XXX] for [AssetName]"

### 2.3 Asset Export
**Test Case**: Export asset versions
- **Steps**:
  1. Select an asset with versions
  2. Right-click on a version → "Export"
  3. Choose export location
  4. Confirm export
- **Expected Result**:
  - Version file copied to export location
  - Log shows "Exported version to: [Path]"

## 3. Shot Management Tests

### 3.1 Shot Creation
**Test Case**: Create shots in sequences
- **Steps**:
  1. Load test project
  2. Right-click on "Shots" → "Create Shot"
  3. Fill shot details:
     - Sequence: "SQ001"
     - Shot: "SH001"
     - Description: "Opening shot"
     - FPS: 24
     - Resolution: 1920x1080
  4. Click "Create"
  5. Create additional shots: SQ001_SH002, SQ002_SH001
- **Expected Result**:
  - Shot directories created in correct sequence folders
  - Shots appear in shot list
  - Log shows "Created shot: [Sequence]/[Shot]"

### 3.2 Shot Versioning
**Test Case**: Create shot versions for different departments
- **Steps**:
  1. Select a shot
  2. Create version for "Animation" department
  3. Create version for "Lighting" department
  4. Create version for "Compositing" department
- **Expected Result**:
  - Versions created with department-specific naming
  - Each department can have independent versioning
  - Log shows version creation for each department

## 4. File System Integration Tests

### 4.1 File System Scanning
**Test Case**: Scan and sync with file system
- **Steps**:
  1. Manually create files in project directories
  2. Click "Refresh" or "Scan Filesystem"
  3. Verify files are detected
- **Expected Result**:
  - New files detected and catalogued
  - File system matches project database
  - Log shows "Filesystem scan completed"

### 4.2 File Operations
**Test Case**: File operations within project
- **Steps**:
  1. Right-click on a version file
  2. Test "Open File" option
  3. Test "Copy Path" option
  4. Test "Delete Version" option
- **Expected Result**:
  - Files open in appropriate applications
  - Paths copied to clipboard
  - Versions deleted with confirmation
  - Log shows operation results

## 5. UI and Navigation Tests

### 5.1 Dock Panel Management
**Test Case**: Show/hide dock panels
- **Steps**:
  1. Test "View" menu options
  2. Toggle Asset Manager dock
  3. Toggle Shot Manager dock
  4. Toggle Log dock
  5. Toggle Version Manager dock
- **Expected Result**:
  - Panels show/hide correctly
  - Layout persists between sessions
  - No UI glitches or crashes

### 5.2 Context Menus
**Test Case**: Right-click context menus
- **Steps**:
  1. Right-click on different items:
     - Project root
     - Asset categories
     - Individual assets
     - Shots
     - Versions
  2. Verify appropriate menu options appear
- **Expected Result**:
  - Context menus show relevant options
  - All menu actions work correctly
  - No missing or broken menu items

## 6. Integration Tests

### 6.1 Maya Integration
**Test Case**: Launch Maya with project context
- **Steps**:
  1. Load test project
  2. Click "Launch Maya" button
  3. Verify Maya opens with correct project settings
- **Expected Result**:
  - Maya launches successfully
  - Project workspace set correctly
  - Vogue Manager Maya tools available
  - Log shows "Maya launched"

### 6.2 API Server
**Test Case**: Start API server
- **Steps**:
  1. Click "Start API Server" button
  2. Verify server starts
  3. Test API endpoints (if implemented)
- **Expected Result**:
  - Server starts without errors
  - API endpoints respond correctly
  - Log shows server status

## 7. Error Handling Tests

### 7.1 Invalid Project Paths
**Test Case**: Handle invalid project paths
- **Steps**:
  1. Try to load project from non-existent path
  2. Try to create project in read-only directory
  3. Try to access corrupted pipeline.json
- **Expected Result**:
  - Appropriate error messages shown
  - Application doesn't crash
  - Log shows error details

### 7.2 File Permission Issues
**Test Case**: Handle file permission errors
- **Steps**:
  1. Create project in location with limited permissions
  2. Try to create versions in read-only directories
  3. Try to delete files without permissions
- **Expected Result**:
  - Permission errors handled gracefully
  - User informed of permission issues
  - Application remains stable

## 8. Performance Tests

### 8.1 Large Project Handling
**Test Case**: Handle projects with many assets/shots
- **Steps**:
  1. Create project with 100+ assets
  2. Create project with 50+ shots
  3. Create multiple versions for each
  4. Test UI responsiveness
- **Expected Result**:
  - UI remains responsive
  - Loading times acceptable
  - Memory usage reasonable
  - No crashes or freezes

### 8.2 File System Performance
**Test Case**: Handle large file operations
- **Steps**:
  1. Create versions with large files (100MB+)
  2. Export multiple large versions
  3. Scan file system with many files
- **Expected Result**:
  - Operations complete successfully
  - Progress indicators shown
  - No timeouts or failures

## 9. Cross-Platform Tests

### 9.1 Windows Compatibility
**Test Case**: Test on Windows systems
- **Steps**:
  1. Run all above tests on Windows
  2. Test path handling (backslashes)
  3. Test Windows-specific file operations
- **Expected Result**:
  - All functionality works on Windows
  - Paths handled correctly
  - No platform-specific issues

### 9.2 File Path Handling
**Test Case**: Test various path formats
- **Steps**:
  1. Use paths with spaces
  2. Use paths with special characters
  3. Use very long paths
  4. Use network paths (UNC)
- **Expected Result**:
  - All path types handled correctly
  - No path-related errors
  - Files accessible regardless of path format

## 10. Data Integrity Tests

### 10.1 Project File Validation
**Test Case**: Validate pipeline.json integrity
- **Steps**:
  1. Manually edit pipeline.json
  2. Introduce syntax errors
  3. Remove required fields
  4. Test project loading
- **Expected Result**:
  - Invalid files detected
  - Appropriate error messages
  - Fallback to default values where possible

### 10.2 Version File Integrity
**Test Case**: Handle missing or corrupted version files
- **Steps**:
  1. Delete version files manually
  2. Corrupt version files
  3. Test version operations
- **Expected Result**:
  - Missing files detected
  - Corrupted files handled
  - Database remains consistent

## Test Execution Notes

1. **Test Environment**: Use dedicated test directories to avoid affecting real projects
2. **Test Data**: Create realistic test files (Maya scenes, textures, etc.)
3. **Logging**: Monitor application logs during all tests
4. **Regression**: Re-run tests after any code changes
5. **Documentation**: Document any issues found and their resolutions

## Success Criteria

- All test cases pass without errors
- No application crashes or freezes
- UI remains responsive during all operations
- File system operations complete successfully
- Error handling works appropriately
- Performance meets acceptable standards
- Cross-platform compatibility maintained
