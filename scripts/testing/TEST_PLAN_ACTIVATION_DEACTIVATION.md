# Test Plan: Activation/Deactivation Functionality
## Club-Admin Perspective

### Test Environment
- **URL**: https://repwarrior.net
- **Test User**: `test-club-admin@repwarrior.net`
- **Password**: `IolT#X7lYAA0qz5`

---

## Test Suite 0: Prerequisites - Create Test Data

### Test 0.1: Create a Test Team
**Objective**: Create a team for testing activation/deactivation

**Steps**:
1. Log in as club-admin
2. Navigate to "Teams" tab
3. Click "Create New Team" button
4. Enter team name: "Test Team - Activation"
5. Click "Create Team"
6. Verify team appears in the list
7. Note the team ID for later tests

**Expected**:
- Team is created successfully
- Team appears in the teams list
- Team has "Active" status badge (green)
- Team has "Deactivate" button visible

**Test Data**:
- Team Name: "Test Team - Activation"
- Team ID: [Record after creation]

---

### Test 0.2: Create a Test Player
**Objective**: Create a player for testing activation/deactivation

**Steps**:
1. Navigate to "Players" tab
2. Click "Add Player" button
3. Fill in player form:
   - Name: "Test Player - Activation"
   - Email: "test-player-1@repwarrior.net"
   - Team: Select "Test Team - Activation" (from Test 0.1)
4. Click "Save" or "Create Player"
5. Verify player appears in the list
6. Note the player ID for later tests

**Expected**:
- Player is created successfully
- Player appears in the players list
- Player has "Active" status badge (green)
- Player has "Deactivate" button visible
- Player has "Invite" button visible (if email provided)

**Test Data**:
- Player Name: "Test Player - Activation"
- Player Email: "test-player-1@repwarrior.net"
- Player ID: [Record after creation]
- Unique Link: [Record after creation]

---

### Test 0.3: Create a Test Coach
**Objective**: Create a coach for testing activation/deactivation

**Steps**:
1. Navigate to "Teams" tab
2. Find "Test Team - Activation" (from Test 0.1)
3. Click "Manage Coaches" button
4. In the "Add Coach" section:
   - Enter Coach Email: "test-coach-1@repwarrior.net"
   - Enter Temporary Password: "TempPass123!2025" (must meet policy: 12+ chars, uppercase, lowercase, number)
5. Click "Add Coach"
6. Wait for coach to appear in the coaches list
7. Verify coach status

**Expected**:
- Coach is created successfully
- Coach appears in the coaches list
- Coach has "Active" status badge (green)
- Coach has "Deactivate" button visible
- Coach status shows "CONFIRMED" or similar

**Test Data**:
- Coach Email: "test-coach-1@repwarrior.net"
- Coach Password: "TempPass123!2025"
- Coach Status: [Record after creation]

---

## Test Suite 1: Player Activation/Deactivation

### Test 1.1: View Player List with Status
**Objective**: Verify player list displays activation status correctly

**Steps**:
1. Navigate to "Players" tab
2. Verify each player card displays:
   - Player name and email
   - Status badge (green "Active" or gray "Inactive")
   - "Activate" button when inactive
   - "Deactivate" button when active
   - "Invite" button (only visible for active players with email)

**Expected**:
- All players display status badges
- Button text matches player status
- Visual indicators are clear and consistent

**Screenshot**: [Take screenshot of player list]

---

### Test 1.2: Deactivate an Active Player
**Objective**: Verify player deactivation works correctly

**Steps**:
1. Navigate to Players tab
2. Identify "Test Player - Activation" (from Test 0.2) or any active player
3. Verify player shows green "Active" badge
4. Click "Deactivate" button
5. Verify confirmation dialog appears
6. Confirm the action in the dialog
7. Wait for page refresh (or observe loading state)
8. Verify player status updated

**Expected**:
- Confirmation dialog: "Are you sure you want to deactivate [Player Name]?"
- Status changes to "Inactive" (gray badge)
- Button text changes to "Activate"
- "Invite" button disappears
- Player remains in the list
- No errors displayed

**API Verification** (DevTools → Network):
- Method: `DELETE`
- Endpoint: `/admin/players/{playerId}`
- Status Code: `200`
- Response includes success message

---

### Test 1.3: Activate an Inactive Player
**Objective**: Verify player activation works correctly

**Steps**:
1. Navigate to Players tab
2. Identify an inactive player (gray "Inactive" badge)
3. Click "Activate" button
4. Verify confirmation dialog appears
5. Confirm the action in the dialog
6. Wait for page refresh
7. Verify player status updated

**Expected**:
- Confirmation dialog: "Are you sure you want to activate [Player Name]?"
- Status changes to "Active" (green badge)
- Button text changes to "Deactivate"
- "Invite" button appears (if player has email)
- Player remains in the list
- No errors displayed

**API Verification** (DevTools → Network):
- Method: `DELETE` (toggles status)
- Endpoint: `/admin/players/{playerId}`
- Status Code: `200`
- Response includes success message

---

### Test 1.4: Cancel Activation/Deactivation
**Objective**: Verify cancel action works correctly

**Steps**:
1. Navigate to Players tab
2. Click "Deactivate" or "Activate" on any player
3. Click "Cancel" in the confirmation dialog
4. Verify no changes occurred

**Expected**:
- Dialog closes
- Player status remains unchanged
- No API call made (check Network tab)

---

### Test 1.5: Update Player with isActive Field
**Objective**: Verify player update endpoint accepts isActive field

**Steps**:
1. Open DevTools → Network tab
2. Navigate to Players tab
3. Edit a player (click "Edit" button)
4. Modify player name or email
5. In Network tab, verify the API call includes `isActive` field support
6. Save changes

**Expected**:
- API call: `PUT /admin/players/{playerId}`
- Request body can include `isActive: true/false`
- Status Code: `200`
- Response includes updated player object

---

## Test Suite 2: Team Activation/Deactivation

### Test 2.1: View Team List with Status
**Objective**: Verify team list displays activation status correctly

**Steps**:
1. Navigate to "Teams" tab
2. Verify each team card displays:
   - Team name and ID
   - Status badge next to team name (green "Active" or gray "Inactive")
   - "Activate" button when inactive
   - "Deactivate" button when active
   - "Edit" and "Manage Coaches" buttons

**Expected**:
- All teams display status badges
- Button text matches team status
- Visual indicators are clear and consistent

**Screenshot**: [Take screenshot of team list]

---

### Test 2.2: Deactivate an Active Team
**Objective**: Verify team deactivation works correctly

**Steps**:
1. Navigate to Teams tab
2. Identify "Test Team - Activation" (from Test 0.1) or any active team
3. Verify team shows green "Active" badge
4. Click "Deactivate" button
5. Verify confirmation dialog appears
6. Confirm the action in the dialog
7. Wait for page refresh
8. Verify team status updated

**Expected**:
- Confirmation dialog: "Are you sure you want to deactivate '[Team Name]'?"
- Status changes to "Inactive" (gray badge)
- Button text changes to "Activate"
- Team remains in the list
- No errors displayed

**API Verification** (DevTools → Network):
- Method: `PUT`
- Endpoint: `/admin/teams/{teamId}/deactivate`
- Status Code: `200`
- Response includes team object and success message

---

### Test 2.3: Activate an Inactive Team
**Objective**: Verify team activation works correctly

**Steps**:
1. Navigate to Teams tab
2. Identify an inactive team (gray "Inactive" badge)
3. Click "Activate" button
4. Verify confirmation dialog appears
5. Confirm the action in the dialog
6. Wait for page refresh
7. Verify team status updated

**Expected**:
- Confirmation dialog: "Are you sure you want to activate '[Team Name]'?"
- Status changes to "Active" (green badge)
- Button text changes to "Deactivate"
- Team remains in the list
- No errors displayed

**API Verification** (DevTools → Network):
- Method: `PUT`
- Endpoint: `/admin/teams/{teamId}/activate`
- Status Code: `200`
- Response includes team object and success message

---

### Test 2.4: Update Team with isActive Field
**Objective**: Verify team update endpoint accepts isActive field

**Steps**:
1. Open DevTools → Network tab
2. Navigate to Teams tab
3. Edit a team (click "Edit" button)
4. Modify team name
5. In Network tab, verify the API call can include `isActive` field
6. Save changes

**Expected**:
- API call: `PUT /admin/teams/{teamId}`
- Request body can include `isActive: true/false`
- Status Code: `200`
- Response includes updated team object

---

### Test 2.5: Team Creation Sets isActive Default
**Objective**: Verify new teams are created as active by default

**Steps**:
1. Navigate to Teams tab
2. Create a new team:
   - Click "Create New Team"
   - Enter team name: "Test Team - Default Active"
   - Click "Create Team"
3. Verify the newly created team status

**Expected**:
- Team is created successfully
- Team has "Active" status badge (green) by default
- Team has "Deactivate" button visible

---

## Test Suite 3: Coach Activation/Deactivation

### Test 3.1: View Coach List with Status
**Objective**: Verify coach list displays activation status correctly

**Steps**:
1. Navigate to "Teams" tab
2. Click "Manage Coaches" on any team
3. Verify each coach in the list displays:
   - Coach email
   - Status badge (green "Active" or gray "Inactive")
   - Cognito status (e.g., "CONFIRMED", "FORCE_CHANGE_PASSWORD")
   - "Activate" button when inactive
   - "Deactivate" button when active
   - "Remove" button

**Expected**:
- All coaches display status badges
- Button text matches coach status
- Visual indicators are clear and consistent

**Screenshot**: [Take screenshot of coach list]

---

### Test 3.2: Deactivate an Active Coach
**Objective**: Verify coach deactivation works correctly

**Steps**:
1. Navigate to Teams tab
2. Expand "Test Team - Activation" (from Test 0.1)
3. Find "test-coach-1@repwarrior.net" (from Test 0.3) or any active coach
4. Verify coach shows green "Active" badge
5. Click "Deactivate" button
6. Verify confirmation dialog appears
7. Confirm the action in the dialog
8. Wait for coach list to refresh
9. Verify coach status updated

**Expected**:
- Confirmation dialog: "Are you sure you want to deactivate [coach email]?"
- Status changes to "Inactive" (gray badge)
- Button text changes to "Activate"
- Coach remains in the list
- Cognito status may show as disabled
- No errors displayed

**API Verification** (DevTools → Network):
- Method: `PUT`
- Endpoint: `/admin/teams/{teamId}/coaches/{coachEmail}/deactivate`
- Status Code: `200`
- Response includes coach object and success message

---

### Test 3.3: Activate an Inactive Coach
**Objective**: Verify coach activation works correctly

**Steps**:
1. Navigate to Teams tab
2. Expand a team with an inactive coach
3. Find an inactive coach (gray "Inactive" badge)
4. Click "Activate" button
5. Verify confirmation dialog appears
6. Confirm the action in the dialog
7. Wait for coach list to refresh
8. Verify coach status updated

**Expected**:
- Confirmation dialog: "Are you sure you want to activate [coach email]?"
- Status changes to "Active" (green badge)
- Button text changes to "Deactivate"
- Coach remains in the list
- Cognito status shows as enabled
- No errors displayed

**API Verification** (DevTools → Network):
- Method: `PUT`
- Endpoint: `/admin/teams/{teamId}/coaches/{coachEmail}/activate`
- Status Code: `200`
- Response includes coach object and success message

---

### Test 3.4: Coach Creation and Immediate Status
**Objective**: Verify newly created coaches are active by default

**Steps**:
1. Navigate to Teams tab
2. Expand a team
3. Add a new coach:
   - Enter email: "test-coach-new@repwarrior.net"
   - Enter temporary password: "TempPass123!2025"
   - Click "Add Coach"
4. Wait for coach to appear in list
5. Verify coach status immediately after creation

**Expected**:
- Coach is created successfully
- Coach appears in the coaches list
- Coach has "Active" status badge (green) by default
- Coach has "Deactivate" button visible

---

## Test Suite 4: Integration & Edge Cases

### Test 4.1: Multiple Rapid Toggles
**Objective**: Verify system handles rapid status changes

**Steps**:
1. Navigate to Players tab
2. Select a player
3. Rapidly toggle status: activate → deactivate → activate
4. Verify each toggle updates correctly
5. Repeat for a team and coach

**Expected**:
- Each toggle updates status correctly
- No errors or race conditions
- Final status matches last action

---

### Test 4.2: Error Handling - Network Failure
**Objective**: Verify graceful error handling

**Steps**:
1. Open DevTools → Network tab
2. Enable "Offline" mode (or throttle network)
3. Navigate to Players tab
4. Try to deactivate a player
5. Observe error handling
6. Re-enable network
7. Verify player status unchanged

**Expected**:
- Error message displayed to user
- Player status remains unchanged
- User can retry after network restored

---

### Test 4.3: Visual Consistency Check
**Objective**: Verify consistent UI design across all sections

**Steps**:
1. Navigate through Players, Teams, and Coaches sections
2. Compare visual elements:
   - Status badge colors (green=active, gray=inactive)
   - Button styling and positioning
   - Status badge positioning relative to names/emails
   - Confirmation dialog styling

**Expected**:
- Consistent color scheme across all sections
- Consistent button styling
- Status badges positioned consistently
- Professional, polished appearance

**Screenshots**: [Take screenshots of each section for comparison]

---

### Test 4.4: Filtering Behavior in Admin Views
**Objective**: Verify inactive entities remain visible to admins

**Steps**:
1. Deactivate a player
2. Verify player still appears in admin Players list
3. Deactivate a team
4. Verify team still appears in admin Teams list
5. Deactivate a coach
6. Verify coach still appears in team's coach list

**Expected**:
- Inactive entities remain visible in admin views
- Only player-facing queries filter inactive entities
- Admins can see and manage all entities regardless of status

---

### Test 4.5: Status Persistence After Page Refresh
**Objective**: Verify status persists correctly

**Steps**:
1. Navigate to Players tab
2. Deactivate a player
3. Refresh the page (F5)
4. Verify player status remains "Inactive"
5. Repeat for team and coach

**Expected**:
- Status persists after page refresh
- Status badges display correctly after refresh
- Buttons show correct text after refresh

---

## Test Suite 5: UI/UX Verification

### Test 5.1: Button States and Loading Indicators
**Objective**: Verify proper loading states during operations

**Steps**:
1. Navigate to Players tab
2. Open DevTools → Network tab
3. Throttle network to "Slow 3G"
4. Click "Deactivate" on a player
5. Observe button state during API call
6. Verify loading indicator or disabled state

**Expected**:
- Button shows loading state or is disabled during operation
- User cannot click button multiple times
- Clear feedback that operation is in progress

---

### Test 5.2: Status Badge Positioning and Visibility
**Objective**: Verify status badges are clearly visible

**Steps**:
1. Check Players tab - status badges on player cards
2. Check Teams tab - status badges next to team names
3. Check Teams → Coaches - status badges next to coach emails
4. Verify badges are:
   - Clearly visible
   - Properly positioned
   - Not overlapping other elements
   - Color-coded correctly

**Expected**:
- Status badges are clearly visible in all locations
- Badges don't overlap with other UI elements
- Colors are distinct and accessible

**Screenshots**: [Take screenshots showing badge positioning]

---

### Test 5.3: Responsive Design
**Objective**: Verify UI works on different screen sizes

**Steps**:
1. Test on desktop viewport (1920x1080 or full browser window)
2. Resize browser to tablet viewport (768px width)
3. Resize browser to mobile viewport (375px width)
4. Verify at each size:
   - Buttons remain accessible
   - Status badges remain visible
   - Text is readable
   - Layout doesn't break

**Expected**:
- UI remains functional on all screen sizes
- Buttons and badges remain accessible
- Text remains readable
- No horizontal scrolling required

**Screenshots**: [Take screenshots at different viewport sizes]

---

### Test 5.4: Confirmation Dialog Clarity
**Objective**: Verify confirmation dialogs are clear and informative

**Steps**:
1. Test confirmation dialogs for:
   - Player activation/deactivation
   - Team activation/deactivation
   - Coach activation/deactivation
2. Verify each dialog:
   - Shows correct entity name
   - Shows correct action (activate/deactivate)
   - Has clear "OK" and "Cancel" options

**Expected**:
- Dialogs clearly state what will happen
- Entity names are displayed correctly
- Actions are unambiguous
- Easy to cancel if clicked by mistake

---

## Test Suite 6: API Endpoint Verification

### Test 6.1: Player Update Endpoint with isActive
**Objective**: Verify player update accepts isActive field

**Steps**:
1. Open DevTools → Network tab
2. Navigate to Players tab
3. Edit a player
4. In the API call, verify request body structure
5. Check if `isActive` field can be included

**Expected**:
- Endpoint: `PUT /admin/players/{playerId}`
- Request body can include `isActive: true/false`
- Response includes updated player with `isActive` field

---

### Test 6.2: Team List Endpoint with active_only Filter
**Objective**: Verify team list supports filtering

**Steps**:
1. Open DevTools → Network tab
2. Navigate to Teams tab
3. Check API call for team list
4. Verify query parameter support for `active_only`

**Expected**:
- Endpoint: `GET /admin/teams?active_only=true`
- Response includes only active teams when filter applied
- Response includes all teams when filter not applied

---

### Test 6.3: Coach Status in List Response
**Objective**: Verify coach list includes activation status

**Steps**:
1. Open DevTools → Network tab
2. Navigate to Teams tab → Manage Coaches
3. Check API response for coach list
4. Verify response includes `enabled` and `isActive` fields

**Expected**:
- Endpoint: `GET /admin/teams/{teamId}/coaches`
- Response includes coach objects with:
  - `email`
  - `username`
  - `status` (Cognito status)
  - `enabled` (boolean)
  - `isActive` (boolean)

---

## Test Results Summary

### Test Execution Log

**Date**: [Date]
**Tester**: [Name]
**Environment**: Production (https://repwarrior.net)
**Browser**: [Browser and version]

### Results by Test Suite

#### Test Suite 0: Prerequisites - Create Test Data
- [ ] Test 0.1: Create a Test Team
- [ ] Test 0.2: Create a Test Player
- [ ] Test 0.3: Create a Test Coach

#### Test Suite 1: Player Activation/Deactivation
- [ ] Test 1.1: View Player List with Status
- [ ] Test 1.2: Deactivate an Active Player
- [ ] Test 1.3: Activate an Inactive Player
- [ ] Test 1.4: Cancel Activation/Deactivation
- [ ] Test 1.5: Update Player with isActive Field

#### Test Suite 2: Team Activation/Deactivation
- [ ] Test 2.1: View Team List with Status
- [ ] Test 2.2: Deactivate an Active Team
- [ ] Test 2.3: Activate an Inactive Team
- [ ] Test 2.4: Update Team with isActive Field
- [ ] Test 2.5: Team Creation Sets isActive Default

#### Test Suite 3: Coach Activation/Deactivation
- [ ] Test 3.1: View Coach List with Status
- [ ] Test 3.2: Deactivate an Active Coach
- [ ] Test 3.3: Activate an Inactive Coach
- [ ] Test 3.4: Coach Creation and Immediate Status

#### Test Suite 4: Integration & Edge Cases
- [ ] Test 4.1: Multiple Rapid Toggles
- [ ] Test 4.2: Error Handling - Network Failure
- [ ] Test 4.3: Visual Consistency Check
- [ ] Test 4.4: Filtering Behavior in Admin Views
- [ ] Test 4.5: Status Persistence After Page Refresh

#### Test Suite 5: UI/UX Verification
- [ ] Test 5.1: Button States and Loading Indicators
- [ ] Test 5.2: Status Badge Positioning and Visibility
- [ ] Test 5.3: Responsive Design
- [ ] Test 5.4: Confirmation Dialog Clarity

#### Test Suite 6: API Endpoint Verification
- [ ] Test 6.1: Player Update Endpoint with isActive
- [ ] Test 6.2: Team List Endpoint with active_only Filter
- [ ] Test 6.3: Coach Status in List Response

### Issues Found

#### Critical Issues
- [None found yet]

#### High Priority Issues
- [None found yet]

#### Medium Priority Issues
- [None found yet]

#### Low Priority Issues
- [None found yet]

### Notes
- [Add any additional notes or observations here]

---

## Appendix: Test Data Reference

### Created Test Entities

**Team**:
- Name: "Test Team - Activation"
- ID: [Record after creation]
- Status: Active (initially)

**Player**:
- Name: "Test Player - Activation"
- Email: "test-player-1@repwarrior.net"
- ID: [Record after creation]
- Unique Link: [Record after creation]
- Status: Active (initially)

**Coach**:
- Email: "test-coach-1@repwarrior.net"
- Password: "TempPass123!2025"
- Status: Active (initially)

---

## Test Execution Instructions

1. **Prerequisites**:
   - Ensure you have club-admin credentials
   - Clear browser cache if needed
   - Open browser DevTools (F12) for API verification

2. **Execution Order**:
   - Start with Test Suite 0 to create test data
   - Proceed through Test Suites 1-6 in order
   - Document results as you go

3. **Documentation**:
   - Take screenshots of UI elements
   - Record API calls in Network tab
   - Note any errors or unexpected behavior
   - Update test results summary

4. **Cleanup** (Optional):
   - After testing, you may want to:
     - Reactivate any deactivated test entities
     - Delete test entities if no longer needed
     - Document final state

