
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

    readonly property int reviewCount: (typeof reviewModel !== "undefined" && reviewModel && reviewModel.count !== undefined) ? reviewModel.count : 0
    readonly property int manualCount: (backend && backend.manualRows) ? backend.manualRows.length : 0
    readonly property string currentFile: (backend && backend.selectedFile) ? backend.selectedFile : ""

    ScrollBar.vertical: ScrollBar {
        id: uploadVbar
        policy: root.contentHeight > root.height ? ScrollBar.AlwaysOn : ScrollBar.AsNeeded
        width: 10
        anchors.right: parent.right
        anchors.rightMargin: 3
        contentItem: Rectangle {
            implicitWidth: 10; radius: 5
            color: Theme.dark
                ? (uploadVbar.pressed ? "#94A3B8" : (uploadVbar.hovered ? "#64748B" : "#475569"))
                : (uploadVbar.pressed ? "#475467" : (uploadVbar.hovered ? "#98A2B3" : "#CBD5E1"))
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

    property string ocrBackendName: "unknown"
    property bool isImageFile: false
    property bool isTextFile: false
    property bool isPdfFile: false

    function updateFileType() {
        var f = (backend ? (backend.selectedFile || "") : "").toLowerCase()
        isImageFile = f.length > 0 && !f.endsWith(".pdf") && !f.endsWith(".txt")
        isTextFile = f.endsWith(".txt")
        isPdfFile = f.endsWith(".pdf")
    }

    // Every value comes from the form the clinician fills in for this
    // patient. Nothing is inherited from the signed-in account: the person
    // operating the app is the doctor, not the patient, so their own age,
    // sex and history must never leak into a report.
    function contextMap() {
        var m = {}

        if (typeof contextPanel !== "undefined" && contextPanel && typeof contextPanel.contextMap === "function") {
            var panelData = contextPanel.contextMap()
            for (var key in panelData) {
                if (panelData.hasOwnProperty(key) && panelData[key] !== null && panelData[key] !== undefined) {
                    m[key] = panelData[key]
                }
            }
        }
        return m
    }

    FileDialog {
        id: fileDialog
        title: "Choose a laboratory report"
        nameFilters: [
            "Laboratory reports (*.png *.jpg *.jpeg *.webp *.pdf *.txt)",
            "Images (*.png *.jpg *.jpeg *.webp)",
            "PDF documents (*.pdf)",
            "Text files (*.txt)",
            "All files (*)"
        ]
        onAccepted: backend.selectFile(selectedFile.toString())
    }

    Connections {
        target: backend
        function onSelectedFileChanged() { root.updateFileType() }
        function onAnalysisReset() {
            root.updateFileType()
            if (typeof contextPanel !== "undefined" && contextPanel) {
                contextPanel.reset()
            }
        }
    }

    Component.onCompleted: {
        var st = (backend && backend.ocrStatus) ? backend.ocrStatus() : {}
        ocrBackendName = (st && st.backend) ? st.backend : "unknown"
        updateFileType()
    }

    ColumnLayout {
        id: content
        width: Math.min(root.width - 60, 1200)
        anchors.horizontalCenter: parent.horizontalCenter
        y: 30
        spacing: 16

        RowLayout {
            Layout.fillWidth: true; spacing: 12
            ToolButton {
                id: uploadBackButton; text: "←"; onClicked: backend.newAnalysis(); font.pixelSize: 20
                contentItem: Text { text: uploadBackButton.text; color: Theme.muted; font.pixelSize: 20; horizontalAlignment: Text.AlignHCenter }
                background: Rectangle { color: uploadBackButton.hovered ? Theme.surfaceAlt : "transparent"; radius: 10 }
            }
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                Text { text: "Upload laboratory report"; color: Theme.text; font.pixelSize: 24; font.bold: true; elide: Text.ElideRight; Layout.fillWidth: true }
                Text { text: "Three quick steps: upload → review → add clinical context → analyze."; color: Theme.muted; font.pixelSize: 12; elide: Text.ElideRight; Layout.fillWidth: true }
            }
            HgButton {
                text: "✕ Remove file"; danger: true
                visible: root.currentFile.length > 0 && root.reviewCount === 0
                // FIX UPL2: don't nuke manual entries when just removing file
                onClicked: { backend.clearFileOnly() }
            }
            Rectangle {
                visible: root.currentFile.length > 0
                implicitWidth: Math.min(fileChipRow.implicitWidth + 24, 200); height: 32; radius: 16
                color: Theme.dark ? "#102A4C" : "#EFF8FF"; border.color: Theme.dark ? "#1D4ED8" : "#B2DDFF"
                RowLayout {
                    id: fileChipRow; anchors.centerIn: parent; spacing: 7
                    Text { text: root.isImageFile ? "🖼" : root.isPdfFile ? "📄" : "📝"; font.pixelSize: 12 }
                    Text {
                        text: (backend && backend.selectedFile ? backend.selectedFile.split(/[\\/]/).pop() : "")
                        color: Theme.dark ? "#93C5FD" : "#175CD3"; font.pixelSize: 10; font.bold: true
                        elide: Text.ElideMiddle; Layout.maximumWidth: 150
                    }
                }
            }
            HgButton {
                id: uploadReportTopBtn
                text: "📤 Browse File"
                primary: true
                implicitHeight: 38
                onClicked: fileDialog.open()
            }
        }

        Rectangle {
            Layout.fillWidth: true; implicitHeight: ocrBannerCol.implicitHeight + 22; radius: 12
            color: Theme.dark
                ? ((backend && backend.ocrError && backend.ocrError.length) ? "#381014" : "#082F1D")
                : ((backend && backend.ocrError && backend.ocrError.length) ? "#FEF3F2" : "#ECFDF3")
            border.color: Theme.dark
                ? ((backend && backend.ocrError && backend.ocrError.length) ? "#7A271A" : "#085D3A")
                : ((backend && backend.ocrError && backend.ocrError.length) ? "#FDA29B" : "#75E0A7")
            ColumnLayout {
                id: ocrBannerCol; anchors.fill: parent; anchors.margins: 11; spacing: 4
                Text {
                    Layout.fillWidth: true; wrapMode: Text.Wrap
                    color: Theme.dark
                        ? ((backend && backend.ocrError && backend.ocrError.length) ? "#FCA5A5" : "#86EFAC")
                        : ((backend && backend.ocrError && backend.ocrError.length) ? "#B42318" : "#067647")
                    font.pixelSize: 10
                    text: (backend && backend.ocrError && backend.ocrError.length) ? "⚠ " + backend.ocrError : "✓ OCR engine ready: " + root.ocrBackendName
                }
                Text {
                    visible: Boolean(backend && backend.ocrAutoRejected > 0); Layout.fillWidth: true; wrapMode: Text.Wrap
                    color: Theme.dark ? "#FBBF24" : "#B54708"; font.pixelSize: 10
                    text: "⚠ " + (backend ? backend.ocrAutoRejected : 0) + " row(s) auto-rejected (unmapped test name or missing value) — they cannot enter the analysis."
                }
            }
        }

        HgCard {
            Layout.fillWidth: true; implicitHeight: step1Col.implicitHeight + 30
            ColumnLayout {
                id: step1Col; anchors.fill: parent; anchors.margins: 18; spacing: 12
                StepHeader { n: "1"; title: "Upload & extract"; hint: "Image, PDF or text report" }
                RowLayout {
                    Layout.fillWidth: true; spacing: 18
                    Rectangle {
                        id: dropBox
                        Layout.preferredWidth: (content.width - 72) * 0.55; implicitHeight: 270; radius: 14
                        color: dropArea.containsDrag ? (Theme.dark ? "#172554" : "#EFF8FF") : (dropBoxMouse.containsMouse ? (Theme.dark ? "#111C33" : "#F4F7FC") : (Theme.dark ? "#0D1424" : "#FBFCFE"))
                        border.color: dropArea.containsDrag || dropBoxMouse.containsMouse ? Theme.accent : Theme.border
                        border.width: dropArea.containsDrag || dropBoxMouse.containsMouse ? 2 : 1
                        clip: true

                        Behavior on border.color { ColorAnimation { duration: 130 } }
                        Behavior on color { ColorAnimation { duration: 130 } }

                        Image {
                            id: img; anchors.fill: parent; anchors.margins: 10
                            visible: root.isImageFile && status === Image.Ready
                            // FIX UPL5: encode spaces/unicode — file:// + local path via encodeURI
                            source: {
                                if (!root.isImageFile || !(backend && backend.selectedFile && backend.selectedFile.length)) return ""
                                // Qt handles file:// URLs; use fromLocalFile if available, else encode
                                var p = backend.selectedFile
                                // Replace backslashes, encode URI
                                return "file://" + encodeURI(p.startsWith("/") ? p : "/" + p.replace(/\\/g, "/"))
                            }
                            fillMode: Image.PreserveAspectFit; horizontalAlignment: Image.AlignHCenter; verticalAlignment: Image.AlignVCenter
                            asynchronous: true; smooth: true; mipmap: true
                            cache: false
                        }
                        BusyIndicator { anchors.centerIn: parent; visible: root.isImageFile && img.status === Image.Loading }

                        Column {
                            anchors.centerIn: parent; spacing: 10; visible: !root.isImageFile
                            Text {
                                anchors.horizontalCenter: parent.horizontalCenter
                                text: (backend && backend.selectedFile && backend.selectedFile.length) ? (root.isPdfFile ? "📄" : "📝") : "⌁"
                                font.pixelSize: 44; color: Theme.accent; opacity: 0.9
                            }
                            Text {
                                anchors.horizontalCenter: parent.horizontalCenter
                                text: (backend && backend.selectedFile && backend.selectedFile.length) ? (root.isTextFile ? "Text report selected" : "PDF report selected") : "Drop a report here or click to browse"
                                color: Theme.text; font.pixelSize: 13; font.weight: Font.DemiBold
                            }
                            Text {
                                anchors.horizontalCenter: parent.horizontalCenter
                                text: "PNG · JPG · WEBP · PDF · TXT"; color: Theme.muted; font.pixelSize: 9
                            }
                            HgButton {
                                anchors.horizontalCenter: parent.horizontalCenter
                                text: (backend && backend.selectedFile && backend.selectedFile.length) ? "Change Report File…" : "📂 Browse Report File"
                                primary: !(backend && backend.selectedFile && backend.selectedFile.length)
                                implicitHeight: 34
                                leftPadding: 16
                                rightPadding: 16
                                onClicked: fileDialog.open()
                            }
                        }

                        MouseArea {
                            id: dropBoxMouse
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            hoverEnabled: true
                            onClicked: fileDialog.open()
                        }

                        DropArea {
                            id: dropArea
                            anchors.fill: parent
                            onDropped: function(drop) {
                                if (drop.hasUrls && drop.urls.length) backend.selectFile(drop.urls[0].toString())
                            }
                        }
                    }
                    ColumnLayout {
                        Layout.fillWidth: true; spacing: 10
                        Text {
                            Layout.fillWidth: true; wrapMode: Text.Wrap
                            text: "The extractor reads test names, values, units and flags. Rows that cannot be mapped to the canonical registry or have no value are rejected automatically."
                            color: Theme.muted; font.pixelSize: 10
                        }
                        HgButton {
                            Layout.fillWidth: true; text: root.reviewCount ? "Extracted ✓" : "Extract report"
                            primary: !root.reviewCount; enabled: root.currentFile.length > 0 && !root.reviewCount
                            onClicked: backend.extractSelectedFile()
                        }
                        HgButton {
                            Layout.fillWidth: true; text: "🗑 Clear extracted"; danger: true; visible: root.reviewCount > 0
                            // FIX UPL2: only clear review, keep manual entries
                            onClicked: backend.clearReviewOnly()
                        }
                        Text {
                            visible: root.manualCount > 0 && root.reviewCount > 0
                            Layout.fillWidth: true; wrapMode: Text.Wrap
                            text: "ℹ️ " + root.manualCount + " manual measurement(s) will be merged with OCR results on confirm."
                            color: Theme.muted; font.pixelSize: 9
                        }
                    }
                }
            }
        }

        HgCard {
            Layout.fillWidth: true; implicitHeight: step2Col.implicitHeight + 30
            ColumnLayout {
                id: step2Col; anchors.fill: parent; anchors.margins: 18; spacing: 10
                StepHeader { n: "2"; title: "Review extracted values"; hint: root.reviewCount ? root.reviewCount + " candidate measurements" : "Waiting for extraction" }
                Rectangle { Layout.fillWidth: true; height: 1; color: Theme.border }
                ListView {
                    Layout.fillWidth: true; Layout.preferredHeight: Math.min(contentHeight, 420)
                    visible: root.reviewCount > 0; model: (typeof reviewModel !== "undefined" && reviewModel) ? reviewModel : null; clip: true; spacing: 8
                    ScrollBar.vertical: ScrollBar {}
                    delegate: Rectangle {
                        id: reviewDelegate
                        required property int index; required property string resultId; required property string decision
                        required property string featureId; required property string featureName
                        required property string value; required property string unit
                        required property real confidence; required property string flag; required property string warning
                        property int pct: Math.round(confidence * 100)
                        width: ListView.view.width; height: delCol.implicitHeight + 22; radius: 13
                        color: decision === "Reject" ? (Theme.dark ? "#381014" : "#FEF3F2") : Theme.surfaceAlt
                        border.color: decision === "Reject" ? "#FDA29B" : decision === "Accept" ? "#A6F0C5" : Theme.border
                        ColumnLayout {
                            id: delCol; anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top; anchors.margins: 11; spacing: 8
                            RowLayout {
                                Layout.fillWidth: true; spacing: 8
                                HgCombo {
                                    Layout.preferredWidth: 96; model: ["Accept", "Edit", "Reject"]
                                    currentIndex: ["Accept", "Edit", "Reject"].indexOf(reviewDelegate.decision)
                                    onActivated: function(i) { backend.updateReviewRow(reviewDelegate.index, "decision", currentText) }
                                }
                                Item {
                                    Layout.fillWidth: true; Layout.preferredHeight: 40
                                    Column {
                                        anchors.verticalCenter: parent.verticalCenter; width: parent.width; spacing: 2
                                        visible: reviewDelegate.decision !== "Edit"
                                        Text { width: parent.width; text: reviewDelegate.featureName; color: Theme.text; font.pixelSize: 12; font.weight: Font.DemiBold; elide: Text.ElideRight }
                                        Text { width: parent.width; text: reviewDelegate.featureId; color: Theme.muted; font.pixelSize: 9; font.family: "monospace"; elide: Text.ElideRight }
                                    }
                                    Loader {
                                        anchors.fill: parent; active: reviewDelegate.decision === "Edit"
                                        sourceComponent: HgCombo {
                                            editable: true; model: (backend && backend.featureOptions) ? backend.featureOptions : []
                                            currentIndex: (backend && backend.featureOptions) ? backend.featureOptions.indexOf(reviewDelegate.featureId) : -1
                                            onActivated: function(i) { if (backend) backend.updateReviewRow(reviewDelegate.index, "featureId", currentText) }
                                            onAccepted: if (backend) backend.updateReviewRow(reviewDelegate.index, "featureId", editText)
                                        }
                                    }
                                }
                                // FIX UPL6: flag now editable — was display-only
                                HgCombo {
                                    Layout.preferredWidth: 90
                                    model: ["", "H", "L", "HH", "LL", "Critical High", "Critical Low", "A", "AA"]
                                    currentIndex: model.indexOf(reviewDelegate.flag)
                                    onActivated: function(i) { backend.updateReviewRow(reviewDelegate.index, "flag", currentText) }
                                    ToolTip.visible: hovered
                                    ToolTip.text: "Lab flag (H/L/Critical) — now editable"
                                }
                                Rectangle {
                                    implicitWidth: confText.implicitWidth + 16; height: 24; radius: 12
                                    color: Theme.dark
                                        ? (reviewDelegate.pct >= 85 ? "#082F1D" : reviewDelegate.pct >= 60 ? "#361E05" : "#381014")
                                        : (reviewDelegate.pct >= 85 ? "#ECFDF3" : reviewDelegate.pct >= 60 ? "#FFFAEB" : "#FEF3F2")
                                    Text {
                                        id: confText; anchors.centerIn: parent; text: reviewDelegate.pct + "%";
                                        color: Theme.dark
                                            ? (reviewDelegate.pct >= 85 ? "#86EFAC" : reviewDelegate.pct >= 60 ? "#FDE68A" : "#FCA5A5")
                                            : (reviewDelegate.pct >= 85 ? "#067647" : reviewDelegate.pct >= 60 ? "#B54708" : "#B42318")
                                        font.pixelSize: 9; font.bold: true
                                    }
                                }
                            }
                            RowLayout {
                                Layout.fillWidth: true; spacing: 8
                                TextField {
                                    Layout.preferredWidth: 100; implicitHeight: 34; text: reviewDelegate.value; placeholderText: "Value"
                                    selectByMouse: true; color: Theme.text
                                    horizontalAlignment: TextInput.AlignLeft
                                    verticalAlignment: TextInput.AlignVCenter
                                    leftPadding: 10; rightPadding: 10
                                    font.family: Theme.fontFamily
                                    font.pixelSize: 13
                                    onEditingFinished: backend.updateReviewRow(reviewDelegate.index, "value", text)
                                    background: Rectangle { radius: 9; color: Theme.surface; border.color: activeFocus ? Theme.accent : Theme.border }
                                }
                                TextField {
                                    Layout.preferredWidth: 100; implicitHeight: 34; text: reviewDelegate.unit; placeholderText: "Unit"
                                    selectByMouse: true; color: Theme.text
                                    horizontalAlignment: TextInput.AlignLeft
                                    verticalAlignment: TextInput.AlignVCenter
                                    leftPadding: 10; rightPadding: 10
                                    font.family: Theme.fontFamily
                                    font.pixelSize: 13
                                    onEditingFinished: backend.updateReviewRow(reviewDelegate.index, "unit", text)
                                    background: Rectangle { radius: 9; color: Theme.surface; border.color: activeFocus ? Theme.accent : Theme.border }
                                }
                                Text {
                                    Layout.fillWidth: true; visible: reviewDelegate.warning.length > 0
                                    text: "⚠ " + reviewDelegate.warning; color: Theme.warning; font.pixelSize: 9; wrapMode: Text.Wrap
                                }
                            }
                        }
                    }
                    footer: Item { width: 1; height: 2 }
                }
                Column {
                    visible: root.reviewCount === 0; Layout.fillWidth: true; spacing: 8
                    Text { anchors.horizontalCenter: parent.horizontalCenter; text: "⌁"; color: Theme.border; font.pixelSize: 36 }
                    Text { anchors.horizontalCenter: parent.horizontalCenter; text: "Extracted values will appear here for your approval."; color: Theme.muted; font.pixelSize: 11 }
                }
            }
        }

        HgCard {
            Layout.fillWidth: true; implicitHeight: step3Col.implicitHeight + 30
            ColumnLayout {
                id: step3Col; anchors.fill: parent; anchors.margins: 18; spacing: 12
                StepHeader { n: "3"; title: "Complete clinical context (Optional)"; hint: "All non-laboratory risk factors. Click 'Load Example' to auto-fill." }
                ClinicalProfilePanel {
                    id: contextPanel
                    Layout.fillWidth: true
                }
            }
        }

        HgButton {
            Layout.fillWidth: true; primary: true; enabled: root.reviewCount > 0
            // FIX UPL3: show merged count
            text: {
                var m = root.manualCount
                var r = root.reviewCount
                if (m > 0) return "Confirm & start analysis → (" + r + " OCR + " + m + " manual)"
                return "Confirm & start analysis → (" + r + " measurements)"
            }
            onClicked: {
                console.log("UploadPage: Starting analysis...")
                var ctx = root.contextMap()
                console.log("UploadPage: Context map =", JSON.stringify(ctx))
                backend.confirmReviewAndAnalyze(ctx)
            }
        }
        RowLayout {
            Layout.fillWidth: true; spacing: 8
            HgButton {
                text: "Add more manually"
                visible: root.reviewCount > 0
                onClicked: backend.navigate("manual")
                ToolTip.visible: hovered
                ToolTip.text: "Go to Manual page to add missing tests — they will be merged on confirm"
            }
            Item { Layout.fillWidth: true }
        }

        Text {
            Layout.fillWidth: true; horizontalAlignment: Text.AlignHCenter; wrapMode: Text.Wrap
            text: "Step 3 is optional — blood values alone are enough. Context only refines risk models that need it."
            color: Theme.muted; font.pixelSize: 9
        }
        Item { Layout.preferredHeight: 10 }
    }

    component StepHeader: RowLayout {
        property string n: ""; property string title: ""; property string hint: ""; spacing: 10
        Rectangle { width: 30; height: 30; radius: 15; color: Theme.accent
            Text { anchors.centerIn: parent; text: n; color: "white"; font.bold: true; font.pixelSize: 13 }
        }
        ColumnLayout { spacing: 1
            Text { text: title; color: Theme.text; font.pixelSize: 15; font.weight: Font.DemiBold }
            Text { text: hint; color: Theme.muted; font.pixelSize: 10 }
        }
    }

    component HgCombo: ComboBox {
        id: combo; implicitHeight: 40; leftPadding: 12; rightPadding: 32; font.family: Theme.fontFamily; font.pixelSize: 12
        contentItem: TextInput {
            leftPadding: 0; rightPadding: 0; text: combo.editable ? combo.editText : combo.displayText
            font: combo.font; color: Theme.text
            horizontalAlignment: TextInput.AlignLeft
            verticalAlignment: Text.AlignVCenter
            readOnly: !combo.editable; selectByMouse: combo.editable; clip: true; cursorVisible: combo.editable && activeFocus
            onTextEdited: combo.editText = text
        }
        background: Rectangle {
            implicitHeight: 40; radius: 10
            color: combo.pressed || combo.hovered ? Theme.surfaceAlt : Theme.surface
            border.color: combo.activeFocus || combo.pressed ? Theme.accent : Theme.border; border.width: combo.activeFocus ? 1.5 : 1
            Behavior on border.color { ColorAnimation { duration: 120 } }
        }
        indicator: Item {
            implicitWidth: 28; implicitHeight: combo.height; anchors.right: parent.right
            Text {
                anchors.centerIn: parent; text: "▾"; font.pixelSize: 10; color: combo.activeFocus ? Theme.accent : Theme.muted
                rotation: combo.pressed ? -180 : 0; Behavior on rotation { NumberAnimation { duration: 130 } }
            }
        }
        popup: Popup {
            y: combo.height + 4; width: combo.width; implicitHeight: Math.min(contentItem.implicitHeight + 12, 320); padding: 6
            background: Rectangle { radius: 10; color: Theme.surface; border.color: Theme.border }
            contentItem: ListView {
                clip: true; implicitHeight: contentHeight; model: combo.popup.visible ? combo.delegateModel : null
                currentIndex: combo.highlightedIndex; ScrollIndicator.vertical: ScrollIndicator {}
            }
        }
        delegate: ItemDelegate {
            id: opt; width: ListView.view ? ListView.view.width : combo.width; implicitHeight: 36
            hoverEnabled: true; highlighted: combo.highlightedIndex === index
            contentItem: Text {
                leftPadding: 8; rightPadding: 8; verticalAlignment: Text.AlignVCenter; elide: Text.ElideRight; font: combo.font
                color: opt.highlighted ? Theme.text : Theme.muted
                text: modelData !== undefined && modelData !== null ? String(modelData) : ""
            }
            background: Rectangle { radius: 8; color: opt.highlighted || opt.hovered ? Theme.surfaceAlt : "transparent" }
        }
    }
}

