import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"
import ".."

Flickable {
    id: root
    contentWidth: width
    contentHeight: content.implicitHeight + 60
    clip: true
    boundsBehavior: Flickable.StopAtBounds

    ScrollBar.vertical: ScrollBar {
        id: guideVbar
        policy: root.contentHeight > root.height ? ScrollBar.AlwaysOn : ScrollBar.AsNeeded
        width: 10
        anchors.right: parent.right
        anchors.rightMargin: 3
        contentItem: Rectangle {
            implicitWidth: 10; radius: 5
            color: Theme.dark
                ? (guideVbar.pressed ? "#94A3B8" : (guideVbar.hovered ? "#64748B" : "#475569"))
                : (guideVbar.pressed ? "#475467" : (guideVbar.hovered ? "#98A2B3" : "#CBD5E1"))
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

    property var detail: null

    ColumnLayout {
        id: content
        width: Math.min(root.width - 52, 1300)
        anchors.horizontalCenter: parent.horizontalCenter
        y: 26
        spacing: 12

        // ============================================================
        // HEADER
        // ============================================================
        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            ToolButton {
                id: guidelinesBack
                text: "←"
                onClicked: backend.navigate("home")
                font.pixelSize: 20
                background: Rectangle { color: guidelinesBack.hovered ? Theme.surfaceAlt : "transparent"; radius: 10 }
            }

            ColumnLayout {
                spacing: 2
                Text { text: "Disease & Guideline Registry"; color: Theme.text; font.pixelSize: 26; font.bold: true }
                Text { text: "Browse diseases, candidate rules, clinical concepts and official guideline sources."; color: Theme.muted; font.pixelSize: 12 }
            }

            Item { Layout.fillWidth: true }

            // آمار کلی رجیستری
            Repeater {
                model: [
                    { n: backend ? backend.diseaseCount : 0, label: "diseases" },
                    { n: backend ? backend.ruleCount : 0, label: "candidate rules" },
                    { n: backend ? backend.sourceCount : 0, label: "guideline sources" }
                ]
                delegate: Rectangle {
                    required property var modelData
                    implicitWidth: countText.implicitWidth + 22
                    height: 30
                    radius: 15
                    color: "#EFF8FF"
                    Text {
                        id: countText
                        anchors.centerIn: parent
                        text: (modelData.n || 0).toLocaleString() + " " + modelData.label
                        color: "#175CD3"
                        font.pixelSize: 10
                        font.bold: true
                    }
                }
            }
        }

        // ============================================================
        // SEARCH
        // ============================================================
        TextField {
            id: guidelineSearch
            Layout.fillWidth: true
            implicitHeight: 44
            placeholderText: "Search diseases… (diabetes, anemia, leukemia, CKD)"
            color: Theme.text
            placeholderTextColor: Theme.muted
            horizontalAlignment: TextInput.AlignLeft
            verticalAlignment: TextInput.AlignVCenter
            leftPadding: 14
            rightPadding: guidelineSearchClearBtn.visible ? 36 : 14
            font.family: Theme.fontFamily
            font.pixelSize: 13
            onTextChanged: guidelineSearchDelay.restart()
            background: Rectangle { radius: 12; color: Theme.surface; border.color: guidelineSearch.activeFocus ? Theme.accent : Theme.border }

            ToolButton {
                id: guidelineSearchClearBtn
                visible: guidelineSearch.text.length > 0
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
                    color: guidelineSearchClearBtn.hovered ? (Theme.dark ? "#334155" : "#E2E8F0") : "transparent"
                }
                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    acceptedButtons: Qt.NoButton
                }
                onClicked: {
                    guidelineSearch.text = ""
                    guidelineSearch.forceActiveFocus()
                }
            }
        }

        Timer {
            id: guidelineSearchDelay
            interval: 180
            repeat: false
            onTriggered: backend.searchDiseases(guidelineSearch.text)
        }

        // ============================================================
        // INFO BAR
        // ============================================================
        Row {
            Layout.fillWidth: true
            spacing: 12
            Text {
                text: (backend && backend.diseaseRows ? backend.diseaseRows.length : 0) + " diseases shown"
                color: Theme.muted
                font.pixelSize: 10
            }
            Text {
                text: "Click a disease to view its candidate rules, sources and Wikipedia link."
                color: Theme.muted
                font.pixelSize: 10
            }
        }

        // ============================================================
        // MAIN CONTENT — لیست بیماری‌ها + جزئیات
        // ============================================================
        RowLayout {
            Layout.fillWidth: true
            implicitHeight: 640
            spacing: 14

            // --------------------------------------------------------
            // LEFT: لیست بیماری‌ها (Diseases)
            // --------------------------------------------------------
            ListView {
                Layout.preferredWidth: Math.max(340, Math.round(root.width * 0.36))
                Layout.maximumWidth: 480
                implicitHeight: 640
                model: backend ? backend.diseaseRows : []
                clip: true
                spacing: 8
                ScrollBar.vertical: ScrollBar {}

                // Empty state
                Rectangle {
                    anchors.fill: parent
                    visible: (backend && backend.diseaseRows ? backend.diseaseRows.length : 0) === 0
                    color: "transparent"
                    Column {
                        anchors.centerIn: parent
                        spacing: 8
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: "▣"
                            color: Theme.muted
                            font.pixelSize: 38
                        }
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: guidelineSearch.text.length > 0
                                  ? "No matching diseases"
                                  : "Loading diseases…"
                            color: Theme.text
                            font.pixelSize: 16
                            font.weight: Font.DemiBold
                        }
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: guidelineSearch.text.length > 0
                                  ? "Try another disease name or concept."
                                  : "The registry is being indexed. Please wait."
                            color: Theme.muted
                            font.pixelSize: 11
                            wrapMode: Text.Wrap
                            horizontalAlignment: Text.AlignHCenter
                            Layout.maximumWidth: 400
                        }
                    }
                }

                delegate: HgCard {
                    id: diseaseCard
                    required property var modelData
                    width: ListView.view ? ListView.view.width : 0
                    implicitHeight: 76
                    interactive: true
                    border.color: root.detail && root.detail.diseaseId === modelData.diseaseId ? Theme.accent : Theme.border

                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.detail = backend.diseaseDetail(modelData.diseaseId)
                    }

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 13
                        spacing: 4

                        Text {
                            text: modelData.name || ""
                            color: Theme.text
                            font.pixelSize: 14
                            font.weight: Font.DemiBold
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            Text {
                                text: modelData.domains || ""
                                color: Theme.muted
                                font.pixelSize: 10
                                elide: Text.ElideRight
                                Layout.fillWidth: true
                            }
                            Rectangle {
                                implicitWidth: ruleCountText.implicitWidth + 14
                                height: 20; radius: 10
                                color: "#EFF8FF"
                                Text {
                                    id: ruleCountText
                                    anchors.centerIn: parent
                                    text: (modelData.ruleCount || "0") + " rules"
                                    color: "#175CD3"
                                    font.pixelSize: 9
                                    font.bold: true
                                }
                            }
                        }
                    }
                }
            }

            // --------------------------------------------------------
            // RIGHT: جزئیات بیماری انتخاب‌شده
            // --------------------------------------------------------
            HgCard {
                Layout.fillWidth: true
                implicitHeight: 640

                Flickable {
                    anchors.fill: parent
                    anchors.margins: 18
                    contentWidth: width
                    contentHeight: detailColumn.implicitHeight
                    clip: true
                    ScrollBar.vertical: ScrollBar {}

                    ColumnLayout {
                        id: detailColumn
                        width: parent ? parent.width : 0
                        spacing: 8

                        // Empty state
                        Text {
                            visible: !root.detail
                            text: "Select a disease on the left to inspect its candidate rules, linked guideline sources and Wikipedia reference."
                            color: Theme.muted
                            font.pixelSize: 12
                            wrapMode: Text.Wrap
                            Layout.fillWidth: true
                            Layout.topMargin: 40
                            horizontalAlignment: Text.AlignHCenter
                        }

                        // Detail content
                        ColumnLayout {
                            visible: root.detail !== null && root.detail.found === true
                            Layout.fillWidth: true
                            spacing: 8

                            // ردیف نام بیماری + دکمه ویکی‌پدیا
                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 12
                                Text {
                                    text: root.detail ? (root.detail.name || "") : ""
                                    color: Theme.text
                                    font.pixelSize: 19
                                    font.weight: Font.Bold
                                    Layout.fillWidth: true
                                    wrapMode: Text.Wrap
                                }
                                HgButton {
                                    visible: root.detail && (root.detail.wikipedia_url || "").length > 0
                                    text: "Wikipedia ↗"
                                    onClicked: Qt.openUrlExternally(root.detail.wikipedia_url)
                                }
                            }

                            Text {
                                text: root.detail ? (root.detail.diseaseId || "") : ""
                                color: Theme.muted
                                font.pixelSize: 10
                                font.family: "monospace"
                            }

                            GridLayout {
                                Layout.fillWidth: true
                                columns: 2
                                columnSpacing: 14
                                rowSpacing: 4
                                Repeater {
                                    model: root.detail ? [
                                        { k: "Domains", v: root.detail.domains },
                                        { k: "Clinical priority", v: root.detail.priority },
                                        { k: "Rule coverage", v: root.detail.coverage },
                                        { k: "Evidence level", v: root.detail.evidenceLevel },
                                        { k: "Required features", v: root.detail.requiredFeatures },
                                        { k: "Optional features", v: root.detail.optionalFeatures },
                                        { k: "ICD-10", v: root.detail.icd10 }
                                    ] : []
                                    delegate: RowLayout {
                                        required property var modelData
                                        Layout.fillWidth: true
                                        Text { text: modelData.k + ": "; color: Theme.muted; font.pixelSize: 10 }
                                        Text { text: modelData.v || "—"; color: Theme.text; font.pixelSize: 10; wrapMode: Text.Wrap; Layout.fillWidth: true }
                                    }
                                }
                            }

                            Text {
                                visible: root.detail && (root.detail.coverageReason || "").length > 0
                                text: root.detail ? (root.detail.coverageReason || "") : ""
                                color: Theme.muted
                                font.pixelSize: 10
                                wrapMode: Text.Wrap
                                Layout.fillWidth: true
                            }

                            // Rules list
                            Text {
                                visible: root.detail && (root.detail.rules || []).length > 0
                                text: "CANDIDATE RULES"
                                color: Theme.muted
                                font.pixelSize: 9
                                font.bold: true
                                font.letterSpacing: 1.4
                                Layout.topMargin: 6
                            }
                            Repeater {
                                model: root.detail ? (root.detail.rules || []) : []
                                delegate: Rectangle {
                                    required property var modelData
                                    Layout.fillWidth: true
                                    implicitHeight: ruleCol.implicitHeight + 18
                                    radius: 10
                                    color: Theme.surfaceAlt
                                    border.color: Theme.border

                                    ColumnLayout {
                                        id: ruleCol
                                        anchors.fill: parent
                                        anchors.margins: 9
                                        spacing: 3

                                        RowLayout {
                                            Layout.fillWidth: true
                                            Text { text: modelData.ruleId || ""; color: Theme.text; font.pixelSize: 10; font.family: "monospace"; font.bold: true; Layout.fillWidth: true }
                                            Text { text: modelData.ruleTypeLabel || ""; color: Theme.violet; font.pixelSize: 9 }
                                        }
                                        Text {
                                            text: modelData.expression || ""
                                            color: Theme.text
                                            opacity: 0.85
                                            font.pixelSize: 10
                                            font.family: "monospace"
                                            wrapMode: Text.Wrap
                                            Layout.fillWidth: true
                                        }
                                        Text {
                                            text: (modelData.population || "") + (modelData.sourceIds ? "  ·  " + modelData.sourceIds : "")
                                            color: Theme.muted
                                            font.pixelSize: 9
                                            wrapMode: Text.Wrap
                                            Layout.fillWidth: true
                                        }
                                    }
                                }
                            }

                            // Sources list
                            Text {
                                visible: root.detail && (root.detail.sources || []).length > 0
                                text: "GUIDELINE SOURCES"
                                color: Theme.muted
                                font.pixelSize: 9
                                font.bold: true
                                font.letterSpacing: 1.4
                                Layout.topMargin: 6
                            }
                            Repeater {
                                model: root.detail ? (root.detail.sources || []) : []
                                delegate: Rectangle {
                                    required property var modelData
                                    Layout.fillWidth: true
                                    implicitHeight: srcCol.implicitHeight + 16
                                    radius: 10
                                    color: Theme.surfaceAlt
                                    border.color: Theme.border

                                    ColumnLayout {
                                        id: srcCol
                                        anchors.fill: parent
                                        anchors.margins: 9
                                        spacing: 2

                                        RowLayout {
                                            Layout.fillWidth: true
                                            Text {
                                                text: (modelData.organization || "") + (modelData.year ? " · " + modelData.year : "")
                                                color: Theme.text
                                                font.pixelSize: 11
                                                font.weight: Font.DemiBold
                                                elide: Text.ElideRight
                                                Layout.fillWidth: true
                                            }
                                            Text {
                                                visible: (modelData.url || "").length > 0
                                                text: "Open ↗"
                                                color: Theme.accent
                                                font.pixelSize: 10
                                                font.bold: true
                                                MouseArea {
                                                    anchors.fill: parent
                                                    cursorShape: Qt.PointingHandCursor
                                                    onClicked: Qt.openUrlExternally(modelData.url)
                                                }
                                            }
                                        }
                                        Text {
                                            text: modelData.title || ""
                                            color: Theme.muted
                                            font.pixelSize: 10
                                            wrapMode: Text.Wrap
                                            Layout.fillWidth: true
                                        }
                                    }
                                }
                            }

                            // Safety message
                            Rectangle {
                                visible: root.detail && (root.detail.safety || "").length > 0
                                Layout.fillWidth: true
                                Layout.topMargin: 6
                                implicitHeight: safetyText.implicitHeight + 20
                                radius: 10
                                color: "#FFFAEB"
                                border.color: "#FEC84B"

                                Text {
                                    id: safetyText
                                    anchors.fill: parent
                                    anchors.margins: 10
                                    text: root.detail ? (root.detail.safety || "") : ""
                                    color: "#8A6100"
                                    font.pixelSize: 10
                                    wrapMode: Text.Wrap
                                    verticalAlignment: Text.AlignVCenter
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // ============================================================
    // CONNECTIONS
    // ============================================================
    Connections {
        target: backend
        function onGuidelinesFocusChanged() {
            var fid = backend.guidelineFocus || ""
            if (fid.length)
                root.detail = backend.diseaseDetail(fid)
        }
        // ✅ رفع باگ لود اولیه: پس از آماده‌شدن رجیستری، لیست را پر کن
        function onReadyChanged() {
            if (backend.ready === true)
                backend.searchDiseases(guidelineSearch.text)
        }
    }

    Component.onCompleted: {
        console.log("GuidelinesPage: Component loaded, ready =", backend.ready)
        if (backend.ready === true)
            backend.searchDiseases("")
    }
}