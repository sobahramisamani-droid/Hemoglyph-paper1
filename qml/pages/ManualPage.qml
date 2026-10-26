import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import "../components"
import ".."

Flickable {
    id: root
    contentWidth: width
    contentHeight: content.implicitHeight + 60
    clip: true
    boundsBehavior: Flickable.StopAtBounds

    ScrollBar.vertical: ScrollBar {
        id: manualVbar
        policy: root.contentHeight > root.height ? ScrollBar.AlwaysOn : ScrollBar.AsNeeded
        width: 10
        anchors.right: parent.right
        anchors.rightMargin: 3
        contentItem: Rectangle {
            implicitWidth: 10; radius: 5
            color: Theme.dark
                ? (manualVbar.pressed ? "#94A3B8" : (manualVbar.hovered ? "#64748B" : "#475569"))
                : (manualVbar.pressed ? "#475467" : (manualVbar.hovered ? "#98A2B3" : "#CBD5E1"))
        }
        background: Rectangle { color: Theme.dark ? "#0F172A" : "#F8FAFC"; radius: 5; opacity: 0.5 }
    }

    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.NoButton
        onWheel: function(wheel) {
            var step = 100
            var delta = wheel.angleDelta.y > 0 ? -step : step
            var maxScroll = Math.max(0, root.contentHeight - root.height)
            root.contentY = Math.max(0, Math.min(maxScroll, root.contentY + delta))
        }
    }

    // ================================================================
    // State Management
    // ================================================================
    property string searchQuery: ""
    property string selectedCategory: (backend && backend.featureCategories && backend.featureCategories.length > 0) ? backend.featureCategories[0] : "All Panels (2,045 Features)"
    property int undoStack: 0
    property int redoStack: 0
    property var history: []
    property var redoHistory: []
    property bool hasUnsavedChanges: false
    property string validationMessage: ""
    property string validationType: "" // "success", "warning", "error"

    // ================================================================
    // Keyboard Shortcuts
    // ================================================================
    Keys.onPressed: function(event) {
        if (event.modifiers & Qt.ControlModifier) {
            switch(event.key) {
                case Qt.Key_Z:
                    if (event.modifiers & Qt.ShiftModifier) {
                        redo()
                    } else {
                        undo()
                    }
                    event.accepted = true
                    break
                case Qt.Key_S:
                    if (hasUnsavedChanges) {
                        saveSession()
                    }
                    event.accepted = true
                    break
                case Qt.Key_N:
                    backend.newAnalysis()
                    event.accepted = true
                    break
                case Qt.Key_Return:
                    if (backend.manualRows.length > 0 && !backend.busy) {
                        runAnalysis()
                    }
                    event.accepted = true
                    break
            }
        }
    }

    // ================================================================
    // Functions
    // ================================================================
    // FIX M1/M6: proper undo/redo — only on structural changes, not on every keystroke
    function undo() {
        if (history.length === 0) return
        if (backend && backend.manualRows) redoHistory.push(JSON.parse(JSON.stringify(backend.manualRows)))
        const lastState = history.pop()
        if (backend) backend.restoreManualState(lastState)
        hasUnsavedChanges = history.length > 0
        showValidation("Undo", "info")
    }

    function redo() {
        if (redoHistory.length === 0) return
        if (backend && backend.manualRows) history.push(JSON.parse(JSON.stringify(backend.manualRows)))
        const nextState = redoHistory.pop()
        if (backend) backend.restoreManualState(nextState)
        hasUnsavedChanges = true
        showValidation("Redo", "info")
    }

    function saveState() {
        // FIX M6: deep copy, cap at 50, clear redo
        if (backend && backend.manualRows) history.push(JSON.parse(JSON.stringify(backend.manualRows)))
        if (history.length > 50) history.shift()
        redoHistory = []
        hasUnsavedChanges = true
    }

    function saveSession() {
        if (backend) backend.saveManualSession()
        hasUnsavedChanges = false
        showValidation("Session saved successfully", "success")
    }

    function clearAll() {
        if (!backend || !backend.manualRows || backend.manualRows.length === 0) return
        showConfirmation(
            "Clear all measurements?",
            "This will remove all " + (backend.manualRows ? backend.manualRows.length : 0) + " measurements.",
            function() {
                saveState()
                if (backend) backend.clearManualOnly()
                hasUnsavedChanges = false
                showValidation("All measurements cleared", "info")
            }
        )
    }

    function runAnalysis() {
        if (backend.manualRows.length === 0) {
            showValidation("Please add at least one measurement", "warning")
            return
        }
        const validation = validateMeasurements()
        if (!validation.valid) {
            showValidation(validation.message, "error")
            return
        }
        // FIX M6: don't push history on analyze — it would bloat undo stack
        var ctx = {}
        if (typeof contextPanel !== "undefined" && contextPanel && typeof contextPanel.contextMap === "function") {
            ctx = contextPanel.contextMap()
        }
        backend.analyzeManual(ctx)
    }

    function _isNumeric(s) {
        if (!s || !s.trim) return false
        var t = s.trim().replace(/٫/g, ".").replace(/،/g, ",").replace(/\s/g, "")
        // allow thousands separators
        if (/^\d{1,3}(,\d{3})+(\.\d+)?$/.test(t)) t = t.replace(/,/g, "")
        else t = t.replace(/,/g, ".")
        return !isNaN(Number(t)) && isFinite(Number(t))
    }

    function validateMeasurements() {
        let missingValues = []
        let nonNumeric = []
        let missingUnits = []
        let mRows = (backend && backend.manualRows) ? backend.manualRows : []
        for (let row of mRows) {
            if (!row.value || String(row.value).trim() === "") {
                missingValues.push(row.featureName)
            } else if (!_isNumeric(String(row.value))) {
                nonNumeric.push(row.featureName + " (" + row.value + ")")
            }
            if (!row.unit || String(row.unit).trim() === "") {
                missingUnits.push(row.featureName)
            }
        }
        if (nonNumeric.length > 0) {
            return {
                valid: false,
                message: "Non-numeric values: " + nonNumeric.slice(0, 3).join(", ") +
                    (nonNumeric.length > 3 ? " and " + (nonNumeric.length - 3) + " more" : "") +
                    ". Use dot for decimal (e.g. 12.5). 1,000 is ok for thousands."
            }
        }
        if (missingValues.length > 0) {
            return {
                valid: false,
                message: "Missing values for: " + missingValues.slice(0, 3).join(", ") +
                    (missingValues.length > 3 ? " and " + (missingValues.length - 3) + " more" : "")
            }
        }
        // Units: warn but don't block — backend is strict, we inform user
        if (missingUnits.length > 0) {
            // only block if many missing, otherwise allow with warning
            if (missingUnits.length > 5) {
                return {
                    valid: false,
                    message: missingUnits.length + " measurements are missing units — add units to avoid analysis failure"
                }
            }
        }
        return { valid: true, message: "" }
    }

    function showValidation(message, type) {
        validationMessage = message
        validationType = type
        validationTimer.restart()
    }

    function showConfirmation(title, message, onConfirm) {
        confirmDialog.title = title
        confirmDialog.text = message
        confirmDialog.onAccept = onConfirm
        confirmDialog.open()
    }

    function exportMeasurements() {
        const data = {
            timestamp: new Date().toISOString(),
            measurements: (backend && backend.manualRows) ? backend.manualRows : [],
            context: (typeof contextPanel !== "undefined" && contextPanel) ? contextPanel.contextMap() : {}
        }
        // FIX M1: use proper file dialog for export location
        exportDialog.open()
    }

    function importMeasurements() {
        importDialog.open()
    }

    function _alreadyAdded(fid) {
        let mRows = (backend && backend.manualRows) ? backend.manualRows : []
        for (let r of mRows) {
            if (r.featureId === fid) return true
        }
        return false
    }

    // ================================================================
    // Timers
    // ================================================================
    Timer {
        id: validationTimer
        interval: 4000
        onTriggered: {
            validationMessage = ""
            validationType = ""
        }
    }

    Timer {
        id: featureSearchDelay
        interval: 300
        repeat: false
        onTriggered: backend.searchFeatures(searchQuery, selectedCategory)
    }

    // ================================================================
    // Connections
    // ================================================================
    Connections {
        target: backend
        function onAnalysisReset() {
            searchQuery = ""
            selectedCategory = (backend && backend.featureCategories && backend.featureCategories.length > 0) ? backend.featureCategories[0] : "All Panels (2,045 Features)"
            if (typeof contextPanel !== "undefined" && contextPanel) {
                contextPanel.reset()
            }
            history = []
            redoHistory = []
            hasUnsavedChanges = false
            if (backend) backend.searchFeatures("", selectedCategory)
            console.log("ManualPage: reset by newAnalysis()")
        }
        function onFeatureCategoriesChanged() {
            if (backend && backend.featureCategories && backend.featureCategories.indexOf(selectedCategory) < 0 && backend.featureCategories.length > 0) {
                selectedCategory = backend.featureCategories[0]
            }
        }
        // FIX M6: don't auto-push history on every manualRowsChanged (that was every keystroke)
    }

    // ================================================================
    // Dialogs
    // ================================================================
    FileDialog {
        id: importDialog
        title: "Import Measurements"
        nameFilters: ["JSON files (*.json)", "All files (*)"]
        onAccepted: {
            if (backend) backend.importFromFile(selectedFile)
            showValidation("Measurements imported", "success")
            hasUnsavedChanges = true
        }
    }
    FileDialog {
        id: exportDialog
        title: "Export Measurements"
        fileMode: FileDialog.SaveFile
        defaultSuffix: "json"
        nameFilters: ["JSON files (*.json)"]
        onAccepted: {
            var data = {
                timestamp: new Date().toISOString(),
                measurements: (backend && backend.manualRows) ? backend.manualRows : [],
                context: (typeof contextPanel !== "undefined" && contextPanel) ? contextPanel.contextMap() : {}
            }
            if (backend) backend.exportToFile(JSON.stringify(data, null, 2), selectedFile.toString())
            showValidation("Measurements exported", "success")
        }
    }

    Dialog {
        id: confirmDialog
        title: "Confirm"
        standardButtons: Dialog.Yes | Dialog.No
        modal: true
        property string text: ""
        property var onAccept: null

        ColumnLayout {
            spacing: 12
            Text {
                text: confirmDialog.text
                wrapMode: Text.Wrap
                Layout.fillWidth: true
                color: Theme.text
            }
        }
        onAccepted: {
            if (onAccept) onAccept()
        }
    }

    // ================================================================
    // Main Layout
    // ================================================================
    ColumnLayout {
        id: content
        width: Math.min(root.width - 60, 1400)
        anchors.horizontalCenter: parent.horizontalCenter
        y: 30
        spacing: 16

        // ============================================================
        // Header
        // ============================================================
        RowLayout {
            Layout.fillWidth: true
            spacing: 12

            ToolButton {
                id: backButton
                text: "←"
                onClicked: {
                    if (hasUnsavedChanges) {
                        showConfirmation(
                            "Unsaved changes",
                            "You have unsaved changes. Do you want to discard them?",
                            function() { backend.newAnalysis() }
                        )
                    } else {
                        backend.newAnalysis()
                    }
                }
                font.pixelSize: 20
                contentItem: Text {
                    text: backButton.text
                    color: Theme.muted
                    font.pixelSize: 20
                    horizontalAlignment: Text.AlignHCenter
                }
                background: Rectangle {
                    color: backButton.hovered ? Theme.surfaceAlt : "transparent"
                    radius: 10
                }
                ToolTip.visible: hovered
                ToolTip.text: "Back / New analysis (Ctrl+N)"
            }

            ColumnLayout {
                spacing: 2
                Text {
                    text: "Manual Laboratory Entry"
                    color: Theme.text
                    font.pixelSize: 28
                    font.bold: true
                }
                Text {
                    text: "Search the canonical registry and add measurements you have"
                    color: Theme.muted
                    font.pixelSize: 13
                }
            }

            Item { Layout.fillWidth: true }

            // Action Buttons
            RowLayout {
                spacing: 8
                HgButton {
                    text: "📥 Import"
                    onClicked: importMeasurements()
                    ToolTip.visible: hovered
                    ToolTip.text: "Import measurements from JSON file"
                }
                HgButton {
                    text: "📤 Export"
                    enabled: backend && backend.manualRows.length > 0
                    onClicked: exportMeasurements()
                    ToolTip.visible: hovered
                    ToolTip.text: "Export measurements to JSON file"
                }
                HgButton {
                    text: "↶ Undo"
                    enabled: history.length > 0
                    onClicked: undo()
                    ToolTip.visible: hovered
                    ToolTip.text: "Undo last change (Ctrl+Z)"
                }
                HgButton {
                    text: "↷ Redo"
                    enabled: redoHistory.length > 0
                    onClicked: redo()
                    ToolTip.visible: hovered
                    ToolTip.text: "Redo last change (Ctrl+Shift+Z)"
                }
                HgButton {
                    text: "🗑 Clear All"
                    danger: true
                    enabled: backend && backend.manualRows.length > 0
                    onClicked: clearAll()
                    ToolTip.visible: hovered
                    ToolTip.text: "Remove all measurements"
                }
            }
        }

        // ============================================================
        // Validation Message
        // ============================================================
        Rectangle {
            visible: validationMessage.length > 0
            Layout.fillWidth: true
            implicitHeight: validationText.implicitHeight + 20
            radius: 10
            color: {
                switch(validationType) {
                    case "success": return Theme.dark ? "#082F1D" : "#ECFDF3"
                    case "warning": return Theme.dark ? "#361E05" : "#FFFAEB"
                    case "error": return Theme.dark ? "#381014" : "#FEF3F2"
                    default: return Theme.dark ? "#102A4C" : "#EFF8FF"
                }
            }
            border.color: {
                switch(validationType) {
                    case "success": return "#75E0A7"
                    case "warning": return "#FEC84B"
                    case "error": return "#FDA29B"
                    default: return "#B2DDFF"
                }
            }
            Text {
                id: validationText
                anchors.fill: parent
                anchors.margins: 10
                text: validationMessage
                color: {
                    switch(validationType) {
                        case "success": return "#067647"
                        case "warning": return "#B54708"
                        case "error": return "#B42318"
                        default: return "#175CD3"
                    }
                }
                font.pixelSize: 12
                wrapMode: Text.Wrap
            }
        }

        // ============================================================
        // Clinical Profile Panel
        // ============================================================
        ClinicalProfilePanel {
            id: contextPanel
            Layout.fillWidth: true
        }

        // ============================================================
        // Main Content: Feature Search + Selected Measurements
        // ============================================================
        RowLayout {
            Layout.fillWidth: true
            implicitHeight: 700
            spacing: 18

            /* ================= Feature Registry (Left Side) ================= */
            HgCard {
                Layout.preferredWidth: content.width * 0.42
                implicitHeight: 700

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 18
                    spacing: 12

                    // Header
                    RowLayout {
                        Layout.fillWidth: true
                        Text {
                            text: "FEATURE REGISTRY"
                            color: Theme.muted
                            font.pixelSize: 11
                            font.bold: true
                            font.letterSpacing: 1.5
                        }
                        Item { Layout.fillWidth: true }
                        Text {
                            text: (backend && backend.featureRows ? backend.featureRows.length : 0).toLocaleString() + " features"
                            color: Theme.muted
                            font.pixelSize: 10
                            font.bold: true
                        }
                    }

                    // Search Bar
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8
                        TextField {
                            id: searchField
                            Layout.fillWidth: true
                            implicitHeight: 42
                            placeholderText: "Search 2,045 laboratory features (e.g. FBS, CBC, Lipids, Creatinine)..."
                            color: Theme.text
                            placeholderTextColor: Theme.muted
                            selectByMouse: true
                            horizontalAlignment: TextInput.AlignLeft
                            verticalAlignment: TextInput.AlignVCenter
                            leftPadding: 14
                            rightPadding: searchClearBtn.visible ? 36 : 14
                            font.family: Theme.fontFamily
                            font.pixelSize: 13
                            text: searchQuery
                            onTextChanged: {
                                searchQuery = text
                                featureSearchDelay.restart()
                            }
                            background: Rectangle {
                                radius: 10
                                color: Theme.surfaceAlt
                                border.color: searchField.activeFocus ? Theme.accent : Theme.border
                                border.width: searchField.activeFocus ? 1.5 : 1
                            }
                            Keys.onDownPressed: featureListView.currentIndex = 0

                            ToolButton {
                                id: searchClearBtn
                                visible: searchField.text.length > 0
                                anchors.right: parent.right
                                anchors.rightMargin: 6
                                anchors.verticalCenter: parent.verticalCenter
                                implicitWidth: 26
                                implicitHeight: 26
                                text: "✕"
                                contentItem: Text {
                                    text: parent.text
                                    color: Theme.muted
                                    font.pixelSize: 12
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                                background: Rectangle {
                                    radius: 13
                                    color: searchClearBtn.hovered ? (Theme.dark ? "#334155" : "#E2E8F0") : "transparent"
                                }
                                MouseArea {
                                    anchors.fill: parent
                                    cursorShape: Qt.PointingHandCursor
                                    acceptedButtons: Qt.NoButton
                                }
                                onClicked: {
                                    searchField.text = ""
                                    searchField.forceActiveFocus()
                                }
                            }
                        }
                        HgCombo {
                            id: categoryBox
                            Layout.preferredWidth: 240
                            model: (backend && backend.featureCategories) ? backend.featureCategories : []
                            currentIndex: {
                                var cats = (backend && backend.featureCategories) ? backend.featureCategories : [];
                                var idx = cats.indexOf(selectedCategory);
                                return idx >= 0 ? idx : 0;
                            }
                            onActivated: function(index) {
                                var cats = (backend && backend.featureCategories) ? backend.featureCategories : [];
                                if (index >= 0 && index < cats.length) {
                                    selectedCategory = cats[index]
                                    if (backend) backend.searchFeatures(searchQuery, selectedCategory)
                                }
                            }
                        }
                    }

                    // Feature List
                    ListView {
                        id: featureListView
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        model: (backend && backend.featureRows) ? backend.featureRows : []
                        clip: true
                        spacing: 6
                        ScrollBar.vertical: ScrollBar {}
                        delegate: ItemDelegate {
                            id: featureSearchDelegate
                            required property var modelData
                            property bool alreadyAdded: _alreadyAdded(modelData.featureId)
                            width: ListView.view.width
                            height: 66
                            enabled: !alreadyAdded
                            onClicked: {
                                if (alreadyAdded) return
                                saveState()
                                backend.addManualFeature(modelData.featureId)
                                showValidation("Added: " + modelData.featureName, "success")
                            }
                            contentItem: RowLayout {
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 3
                                    Text {
                                        text: modelData.featureName || ""
                                        color: featureSearchDelegate.alreadyAdded ? (Theme.dark ? "#86EFAC" : "#067647") : Theme.text
                                        font.pixelSize: 13
                                        font.weight: Font.DemiBold
                                        elide: Text.ElideRight
                                        Layout.fillWidth: true
                                    }
                                    Text {
                                        text: (modelData.featureId || "") + " · " + (modelData.category || "uncategorized")
                                        color: featureSearchDelegate.alreadyAdded ? (Theme.dark ? "#A7F3D0" : "#046C4E") : Theme.muted
                                        opacity: featureSearchDelegate.alreadyAdded ? (Theme.dark ? 0.75 : 0.85) : 1.0
                                        font.pixelSize: 9
                                        elide: Text.ElideRight
                                        Layout.fillWidth: true
                                    }
                                }
                                ColumnLayout {
                                    spacing: 2
                                    Text {
                                        text: modelData.unit || ""
                                        color: featureSearchDelegate.alreadyAdded ? (Theme.dark ? "#6EE7B7" : "#046C4E") : Theme.accent
                                        font.pixelSize: 10
                                        font.bold: true
                                        horizontalAlignment: Text.AlignRight
                                        Layout.alignment: Qt.AlignRight
                                    }
                                    Text {
                                        text: featureSearchDelegate.alreadyAdded ? "✓" : "+"
                                        color: featureSearchDelegate.alreadyAdded ? (Theme.dark ? "#34D399" : "#067647") : Theme.violet
                                        font.pixelSize: 22
                                        font.bold: true
                                        horizontalAlignment: Text.AlignRight
                                        Layout.alignment: Qt.AlignRight
                                    }
                                }
                            }
                            background: Rectangle {
                                color: featureSearchDelegate.alreadyAdded ?
                                    (Theme.dark ? "#092F1E" : "#ECFDF3") :
                                    (featureSearchDelegate.hovered ? Theme.surfaceAlt : "transparent")
                                radius: 10
                                border.color: featureSearchDelegate.alreadyAdded ?
                                    (Theme.dark ? "#0D6E43" : "#75E0A7") :
                                    Theme.border
                                border.width: featureSearchDelegate.hovered || featureSearchDelegate.alreadyAdded ? 1 : 0
                            }
                        }
                    }

                    // Empty State
                    Rectangle {
                        visible: !(backend && backend.featureRows && backend.featureRows.length > 0)
                        Layout.fillWidth: true
                        implicitHeight: 120
                        color: "transparent"
                        Column {
                            anchors.centerIn: parent
                            spacing: 6
                            Text {
                                anchors.horizontalCenter: parent.horizontalCenter
                                text: "🔍"
                                font.pixelSize: 32
                                color: Theme.muted
                                opacity: 0.6
                            }
                            Text {
                                anchors.horizontalCenter: parent.horizontalCenter
                                text: searchQuery.length > 0 ? "No features found" : "Start typing to search"
                                color: Theme.muted
                                font.pixelSize: 12
                            }
                        }
                    }
                }
            }

            /* ================= Selected Measurements (Right Side) ================= */
            HgCard {
                Layout.fillWidth: true
                implicitHeight: 700

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 18
                    spacing: 12

                    // Header
                    RowLayout {
                        Layout.fillWidth: true
                        ColumnLayout {
                            spacing: 2
                            Text {
                                text: "SELECTED MEASUREMENTS"
                                color: Theme.muted
                                font.pixelSize: 11
                                font.bold: true
                                font.letterSpacing: 1.5
                            }
                            Text {
                                text: (backend && backend.manualRows ? backend.manualRows.length : 0) + " features"
                                color: Theme.text
                                font.pixelSize: 18
                                font.weight: Font.DemiBold
                            }
                        }
                        Item { Layout.fillWidth: true }

                        // Status Badge
                        Rectangle {
                            visible: Boolean(backend && backend.manualRows && backend.manualRows.length > 0)
                            implicitWidth: readyBadge.implicitWidth + 20
                            height: 28
                            radius: 14
                            color: hasUnsavedChanges
                                ? (Theme.dark ? "#361E05" : "#FFFAEB")
                                : (Theme.dark ? "#082F1D" : "#ECFDF3")
                            border.color: hasUnsavedChanges
                                ? (Theme.dark ? "#78350F" : "#FEDF89")
                                : (Theme.dark ? "#085D3A" : "#75E0A7")
                            Text {
                                id: readyBadge
                                anchors.centerIn: parent
                                text: hasUnsavedChanges ? "Unsaved changes" : "Ready to analyze"
                                color: hasUnsavedChanges
                                    ? (Theme.dark ? "#FDE68A" : "#B54708")
                                    : (Theme.dark ? "#86EFAC" : "#067647")
                                font.pixelSize: 10
                                font.bold: true
                            }
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        height: 1
                        color: Theme.border
                    }

                    // Measurements List
                    ListView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        model: backend ? backend.manualRows : []
                        clip: true
                        spacing: 8
                        ScrollBar.vertical: ScrollBar {}
                        delegate: Rectangle {
                            required property var modelData
                            width: ListView.view.width
                            height: 78
                            radius: 12
                            color: Theme.surfaceAlt
                            border.color: Theme.border
                            RowLayout {
                                anchors.fill: parent
                                anchors.margins: 12
                                spacing: 8
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    Layout.minimumWidth: 80
                                    spacing: 3
                                    Text {
                                        id: fNameText
                                        text: modelData.featureName || ""
                                        color: Theme.text
                                        font.pixelSize: 13
                                        font.weight: Font.DemiBold
                                        elide: Text.ElideRight
                                        Layout.fillWidth: true
                                        ToolTip.visible: nameHover.containsMouse && fNameText.truncated
                                        ToolTip.text: modelData.featureName || ""
                                        MouseArea {
                                            id: nameHover
                                            anchors.fill: parent
                                            hoverEnabled: true
                                            acceptedButtons: Qt.NoButton
                                        }
                                    }
                                    Text {
                                        text: modelData.featureId || ""
                                        color: Theme.muted
                                        font.pixelSize: 9
                                        elide: Text.ElideRight
                                        Layout.fillWidth: true
                                    }
                                }
                                TextField {
                                    id: valueField
                                    Layout.preferredWidth: 95
                                    implicitHeight: 38
                                    placeholderText: "Value"
                                    selectByMouse: true
                                    color: Theme.text
                                    horizontalAlignment: TextInput.AlignLeft
                                    verticalAlignment: TextInput.AlignVCenter
                                    leftPadding: 10
                                    rightPadding: 10
                                    font.family: Theme.fontFamily
                                    font.pixelSize: 13
                                    text: modelData.value || ""
                                    // FIX M2: onEditingFinished instead of onTextChanged — keeps focus
                                    onEditingFinished: {
                                        if (modelData && modelData.featureId) {
                                            backend.updateManualValueByFeatureId(modelData.featureId, text)
                                        }
                                    }
                                    Keys.onReturnPressed: valueField.focus = false
                                    background: Rectangle {
                                        radius: 9
                                        color: Theme.surface
                                        border.color: {
                                            if (valueField.activeFocus) return Theme.accent
                                            if (valueField.text.length > 0 && !_isNumeric(valueField.text)) return "#FDA29B"
                                            return Theme.border
                                        }
                                        border.width: valueField.activeFocus ? 1.5 : 1
                                    }
                                }
                                TextField {
                                    id: unitField
                                    Layout.preferredWidth: 95
                                    implicitHeight: 38
                                    placeholderText: "Unit"
                                    selectByMouse: true
                                    color: Theme.text
                                    horizontalAlignment: TextInput.AlignLeft
                                    verticalAlignment: TextInput.AlignVCenter
                                    leftPadding: 10
                                    rightPadding: 10
                                    font.family: Theme.fontFamily
                                    font.pixelSize: 13
                                    text: modelData.unit || ""
                                    onEditingFinished: {
                                        if (modelData && modelData.featureId) {
                                            backend.updateManualUnitByFeatureId(modelData.featureId, text)
                                        }
                                    }
                                    Keys.onReturnPressed: unitField.focus = false
                                    background: Rectangle {
                                        radius: 9
                                        color: Theme.surface
                                        border.color: unitField.activeFocus ? Theme.accent : Theme.border
                                        border.width: unitField.activeFocus ? 1.5 : 1
                                    }
                                }
                                Button {
                                    id: removeButton
                                    Layout.preferredWidth: 32
                                    Layout.preferredHeight: 32
                                    Layout.alignment: Qt.AlignVCenter
                                    hoverEnabled: true
                                    ToolTip.visible: hovered
                                    ToolTip.text: "Remove this measurement"
                                    
                                    onClicked: {
                                        saveState()
                                        var fid = (modelData && modelData.featureId) ? String(modelData.featureId) : ""
                                        var fName = (modelData && modelData.featureName) ? String(modelData.featureName) : "Measurement"
                                        var idx = (typeof index !== "undefined") ? index : (modelData && modelData.index !== undefined ? modelData.index : 0)
                                        
                                        if (fid.length > 0) {
                                            backend.removeManualFeatureByFeatureId(fid)
                                        } else {
                                            backend.removeManualFeature(idx)
                                        }
                                        showValidation("Removed: " + fName, "info")
                                    }

                                    contentItem: Text {
                                        text: "✕"
                                        color: removeButton.hovered ? "#EF4444" : "#F87171"
                                        font.pixelSize: 14
                                        font.bold: true
                                        horizontalAlignment: Text.AlignHCenter
                                        verticalAlignment: Text.AlignVCenter
                                    }

                                    background: Rectangle {
                                        radius: 8
                                        color: removeButton.hovered
                                            ? (Theme.dark ? "#3B1219" : "#FEF2F2")
                                            : (Theme.dark ? "#26151E" : "#FFF5F5")
                                        border.color: removeButton.hovered
                                            ? (Theme.dark ? "#991B1B" : "#FCA5A5")
                                            : (Theme.dark ? "#4C1D24" : "#FEE2E2")
                                        border.width: 1
                                    }

                                    MouseArea {
                                        anchors.fill: parent
                                        cursorShape: Qt.PointingHandCursor
                                        acceptedButtons: Qt.NoButton
                                    }
                                }
                            }
                        }
                    }

                    // Empty State
                    Rectangle {
                        visible: !(backend && backend.manualRows && backend.manualRows.length > 0)
                        Layout.fillWidth: true
                        implicitHeight: 200
                        color: "transparent"
                        Column {
                            anchors.centerIn: parent
                            spacing: 10
                            Text {
                                anchors.horizontalCenter: parent.horizontalCenter
                                text: "📋"
                                font.pixelSize: 40
                                color: Theme.muted
                                opacity: 0.5
                            }
                            Text {
                                anchors.horizontalCenter: parent.horizontalCenter
                                text: "No measurements selected yet"
                                color: Theme.text
                                font.pixelSize: 14
                                font.weight: Font.DemiBold
                            }
                            Text {
                                anchors.horizontalCenter: parent.horizontalCenter
                                text: "Search and click the + button to add measurements"
                                color: Theme.muted
                                font.pixelSize: 11
                                opacity: 0.8
                                horizontalAlignment: Text.AlignHCenter
                                wrapMode: Text.Wrap
                                Layout.maximumWidth: 300
                            }
                        }
                    }

                    // Run Analysis Button
                    HgButton {
                        Layout.fillWidth: true
                        primary: true
                        // ✅ استفاده از backend.busy به جای isAnalyzing محلی
                        enabled: Boolean(backend && backend.manualRows && backend.manualRows.length > 0 && !backend.busy)
                        text: (backend && backend.busy) ? "⏳ Analyzing..." : "Run Analysis → (Ctrl+Enter)"
                        onClicked: runAnalysis()
                        ToolTip.visible: hovered
                        ToolTip.text: "Analyze " + (backend && backend.manualRows ? backend.manualRows.length : 0) + " measurements"
                    }

                    // Keyboard Shortcuts Help
                    Text {
                        Layout.fillWidth: true
                        text: "Shortcuts: Ctrl+N (New) · Ctrl+Z (Undo) · Ctrl+Shift+Z (Redo) · Ctrl+S (Save) · Ctrl+Enter (Analyze)"
                        color: Theme.muted
                        font.pixelSize: 9
                        horizontalAlignment: Text.AlignHCenter
                        wrapMode: Text.Wrap
                    }
                }
            }
        }
    }

    // ================================================================
    // Initial Load
    // ================================================================
    Component.onCompleted: {
        if (backend && backend.featureCategories && backend.featureCategories.length > 0) {
            selectedCategory = backend.featureCategories[0]
        }
        if (backend) backend.searchFeatures("", selectedCategory)
    }

    // ================================================================
    // ComboBox Component
    // ================================================================
    component HgCombo: ComboBox {
        id: control
        implicitHeight: 42
        leftPadding: 14
        rightPadding: 36
        font.family: Theme.fontFamily
        font.pixelSize: 12

        contentItem: Text {
            leftPadding: 0
            rightPadding: 0
            text: control.displayText
            font: control.font
            color: Theme.text
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }

        background: Rectangle {
            implicitHeight: 42
            radius: 10
            color: control.pressed || control.hovered ? Theme.surfaceAlt : Theme.surface
            border.color: control.activeFocus || control.pressed ? Theme.accent : Theme.border
            border.width: control.activeFocus ? 1.5 : 1
            Behavior on border.color { ColorAnimation { duration: 120 } }
        }

        indicator: Item {
            implicitWidth: 28
            implicitHeight: control.height
            anchors.right: parent.right
            Text {
                anchors.centerIn: parent
                text: "▾"
                font.pixelSize: 11
                color: control.activeFocus ? Theme.accent : Theme.muted
                rotation: control.pressed ? -180 : 0
                Behavior on rotation { NumberAnimation { duration: 130 } }
            }
        }

        popup: Popup {
            y: control.height + 4
            width: control.width
            implicitHeight: Math.min(contentItem.implicitHeight + 12, 320)
            padding: 6
            background: Rectangle {
                radius: 10
                color: Theme.surface
                border.color: Theme.border
            }
            contentItem: ListView {
                clip: true
                implicitHeight: contentHeight
                model: control.popup.visible ? control.delegateModel : null
                currentIndex: control.highlightedIndex
                ScrollIndicator.vertical: ScrollIndicator {}
            }
        }

        delegate: ItemDelegate {
            id: opt
            width: ListView.view ? ListView.view.width : control.width
            implicitHeight: 36
            highlighted: control.highlightedIndex === index
            contentItem: Text {
                leftPadding: 10
                rightPadding: 10
                verticalAlignment: Text.AlignVCenter
                elide: Text.ElideRight
                font: control.font
                color: opt.highlighted ? Theme.text : Theme.muted
                text: modelData !== undefined && modelData !== null ? String(modelData) : ""
            }
            background: Rectangle {
                radius: 8
                color: opt.highlighted || opt.hovered ? Theme.surfaceAlt : "transparent"
            }
        }
    }
}
