import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"
import ".."

Item {
    id: root

    // ================================================================
    // Live stats from backend
    // ================================================================
    readonly property int featCount: (backend ? backend.featureCount : 0) || 0
    readonly property int disCount:  (backend ? backend.diseaseCount : 0) || 0
    readonly property int rulCount:  (backend ? backend.ruleCount : 0) || 0
    readonly property int srcCount:  (backend ? backend.sourceCount : 0) || 0
    readonly property bool engineReady: backend ? (backend.ready === true) : false

    Flickable {
        id: homeFlick
        anchors.fill: parent
        contentWidth: width
        contentHeight: content.implicitHeight + 60
        clip: true
        boundsBehavior: Flickable.StopAtBounds

        ScrollBar.vertical: ScrollBar {
            id: homeVbar
            policy: homeFlick.contentHeight > homeFlick.height ? ScrollBar.AlwaysOn : ScrollBar.AsNeeded
            width: 10
            anchors.right: parent.right
            anchors.rightMargin: 3
            contentItem: Rectangle {
                implicitWidth: 10; radius: 5
                color: Theme.dark
                    ? (homeVbar.pressed ? "#94A3B8" : (homeVbar.hovered ? "#64748B" : "#475569"))
                    : (homeVbar.pressed ? "#475467" : (homeVbar.hovered ? "#98A2B3" : "#CBD5E1"))
            }
            background: Rectangle { color: Theme.dark ? "#0F172A" : "#F8FAFC"; radius: 5; opacity: 0.5 }
        }

        MouseArea {
            anchors.fill: parent
            acceptedButtons: Qt.NoButton
            onWheel: function(wheel) {
                var step = 100
                var delta = wheel.angleDelta.y > 0 ? -step : step
                var maxScroll = Math.max(0, homeFlick.contentHeight - homeFlick.height)
                homeFlick.contentY = Math.max(0, Math.min(maxScroll, homeFlick.contentY + delta))
            }
        }

        ColumnLayout {
            id: content
            width: Math.min(root.width - 72, 1060)
            anchors.horizontalCenter: parent.horizontalCenter
            y: 40
            spacing: 22

            // ============================================================
            //  HERO SECTION
            // ============================================================
            Rectangle {
                Layout.fillWidth: true
                implicitHeight: heroCol.implicitHeight + 64
                radius: 24
                color: Theme.surface
                border.color: Theme.border
                clip: true

                // Decorative gradient circles
                Rectangle {
                    width: 300; height: 300; radius: 150
                    x: parent.width - 100; y: -120
                    gradient: Gradient {
                        GradientStop { position: 0; color: "#1823BFE5" }
                        GradientStop { position: 1; color: "#0023BFE5" }
                    }
                }
                Rectangle {
                    width: 200; height: 200; radius: 100
                    x: -60; y: parent.height - 80
                    gradient: Gradient {
                        GradientStop { position: 0; color: "#127558F5" }
                        GradientStop { position: 1; color: "#007558F5" }
                    }
                }

                ColumnLayout {
                    id: heroCol
                    anchors.centerIn: parent
                    spacing: 16
                    width: parent.width - 80

                    // Animated logo
                    Rectangle {
                        Layout.alignment: Qt.AlignHCenter
                        width: 88; height: 88; radius: 26
                        gradient: Gradient {
                            GradientStop { position: 0; color: Theme.accent }
                            GradientStop { position: 1; color: Theme.violet }
                        }
                        Text {
                            anchors.centerIn: parent
                            text: "🧬"
                            font.pixelSize: 44
                        }
                        SequentialAnimation on scale {
                            loops: Animation.Infinite
                            NumberAnimation { from: 1.0; to: 1.06; duration: 1400; easing.type: Easing.InOutSine }
                            NumberAnimation { from: 1.06; to: 1.0; duration: 1400; easing.type: Easing.InOutSine }
                        }
                    }

                    Text {
                        Layout.alignment: Qt.AlignHCenter
                        text: "HEMOGLYPH"
                        color: Theme.text
                        font.pixelSize: 40
                        font.weight: Font.Bold
                        font.letterSpacing: 6
                    }

                    Text {
                        Layout.alignment: Qt.AlignHCenter
                        text: "Clinical Decision Support & Laboratory Intelligence Suite"
                        color: Theme.muted
                        font.pixelSize: 15
                        horizontalAlignment: Text.AlignHCenter
                        wrapMode: Text.Wrap
                        Layout.maximumWidth: 620
                    }

                    // Developer Badge Pill
                    Rectangle {
                        Layout.alignment: Qt.AlignHCenter
                        implicitWidth: devBadgeRow.implicitWidth + 24
                        height: 28
                        radius: 14
                        color: Theme.dark ? "#1F1B38" : "#F3F0FF"
                        border.color: Theme.violet
                        border.width: 1

                        RowLayout {
                            id: devBadgeRow
                            anchors.centerIn: parent
                            spacing: 6

                            Text {
                                text: "✨"
                                font.pixelSize: 11
                            }
                            Text {
                                text: "Developed by Sobhan Bahrami"
                                color: Theme.violet
                                font.pixelSize: 11
                                font.weight: Font.DemiBold
                                font.letterSpacing: 0.5
                            }
                        }
                    }

                    // Engine status pill
                    Rectangle {
                        Layout.alignment: Qt.AlignHCenter
                        implicitWidth: engineStatusText.implicitWidth + 30
                        height: 32; radius: 16
                        color: root.engineReady ? "#ECFDF3" : "#FFFAEB"
                        border.color: root.engineReady ? "#75E0A7" : "#FEC84B"
                        RowLayout {
                            anchors.centerIn: parent; spacing: 8
                            Rectangle {
                                width: 8; height: 8; radius: 4
                                color: root.engineReady ? Theme.success : Theme.warning
                                SequentialAnimation on opacity {
                                    loops: Animation.Infinite
                                    NumberAnimation { from: 1; to: 0.3; duration: 800 }
                                    NumberAnimation { from: 0.3; to: 1; duration: 800 }
                                }
                            }
                            Text {
                                id: engineStatusText
                                text: root.engineReady
                                    ? "Engine ready"
                                    : (backend ? backend.bootstrapText : "Loading registries…")
                                color: root.engineReady ? "#067647" : "#B54708"
                                font.pixelSize: 10; font.bold: true
                            }
                        }
                    }

                    // CTA buttons
                    RowLayout {
                        Layout.alignment: Qt.AlignHCenter
                        spacing: 14
                        Layout.topMargin: 8

                        HgButton {
                            text: "+ New analysis"
                            primary: true
                            onClicked: backend.navigate("newAnalysis")
                        }
                        HgButton {
                            text: "Upload report"
                            onClicked: backend.navigate("upload")
                        }
                        HgButton {
                            text: "Manual entry"
                            onClicked: backend.navigate("manual")
                        }
                    }
                }
            }

            // ============================================================
            //  LIVE STATISTICS
            // ============================================================
            RowLayout {
                Layout.fillWidth: true
                spacing: 16
                Layout.topMargin: 4

                StatCard {
                    Layout.fillWidth: true
                    icon: "🔬"
                    number: root.featCount
                    label: "Laboratory Features"
                    accent: Theme.accent
                    loading: !root.engineReady
                }
                StatCard {
                    Layout.fillWidth: true
                    icon: "🩺"
                    number: root.disCount
                    label: "Clinical Concepts"
                    accent: Theme.violet
                    loading: !root.engineReady
                }
                StatCard {
                    Layout.fillWidth: true
                    icon: "📐"
                    number: root.rulCount
                    label: "Research Rules"
                    accent: Theme.info
                    loading: !root.engineReady
                }
                StatCard {
                    Layout.fillWidth: true
                    icon: "📚"
                    number: root.srcCount
                    label: "Guideline Sources"
                    accent: Theme.success
                    loading: !root.engineReady
                }
            }

            // ============================================================
            //  CAPABILITIES
            // ============================================================
            RowLayout {
                Layout.fillWidth: true
                spacing: 16

                CapabilityCard {
                    Layout.fillWidth: true
                    icon: "🤖"
                    title: "AI Assistant"
                    desc: "Grounded chatbot explains your results in English or Persian, citing source IDs."
                    onClicked: backend.navigate("chat")
                }
                CapabilityCard {
                    Layout.fillWidth: true
                    icon: "📄"
                    title: "OCR Extraction"
                    desc: "Upload images or PDFs. Every value is reviewed by you before analysis."
                    onClicked: backend.navigate("upload")
                }
                CapabilityCard {
                    Layout.fillWidth: true
                    icon: "📊"
                    title: "Risk Models"
                    desc: "70+ validated global risk equations with full scientific references."
                    onClicked: backend.navigate("riskmodels")
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 16

                CapabilityCard {
                    Layout.fillWidth: true
                    icon: "📋"
                    title: "Guidelines Library"
                    desc: "Browse candidate rules, disease concepts and official guideline sources."
                    onClicked: backend.navigate("guidelines")
                }
                CapabilityCard {
                    Layout.fillWidth: true
                    icon: "🕐"
                    title: "History"
                    desc: "All analyses are auto-saved. Re-open, compare, or continue any session."
                    onClicked: backend.navigate("history")
                }
                CapabilityCard {
                    Layout.fillWidth: true
                    icon: "⚙"
                    title: "Profile & Settings"
                    desc: "Save demographics and medical history for automatic context in every analysis."
                    onClicked: backend.navigate("settings")
                }
            }

            // ============================================================
            //  DISCLAIMER
            // ============================================================
            Rectangle {
                Layout.fillWidth: true
                implicitHeight: disclaimerText.implicitHeight + 24
                radius: 14
                color: "#FFFAEB"
                border.color: "#FEC84B"

                Text {
                    id: disclaimerText
                    anchors.fill: parent
                    anchors.margins: 14
                    wrapMode: Text.Wrap
                    horizontalAlignment: Text.AlignHCenter
                    color: "#8A6100"
                    font.pixelSize: 11
                    font.weight: Font.DemiBold
                    text: "⚠ HEMOGLYPH is a research tool that identifies laboratory criteria and compatible patterns. It does not diagnose disease or prescribe treatment. Always consult a qualified clinician."
                }
            }

            // Footer
            ColumnLayout {
                Layout.alignment: Qt.AlignHCenter
                spacing: 6
                Layout.bottomMargin: 14

                RowLayout {
                    Layout.alignment: Qt.AlignHCenter
                    spacing: 8

                    Text {
                        text: "HEMOGLYPH " + (backend ? (backend.appBuild || "1.3.1") : "1.3.1") + " · Clinical Intelligence Suite"
                        color: Theme.muted
                        font.pixelSize: 11
                    }
                    Text { text: "•"; color: Theme.muted; font.pixelSize: 10 }
                    Text {
                        text: "Engineered & Developed by Sobhan Bahrami"
                        color: Theme.violet
                        font.pixelSize: 11
                        font.weight: Font.DemiBold
                    }
                }

                RowLayout {
                    Layout.alignment: Qt.AlignHCenter
                    spacing: 6

                    Text {
                        text: "Clinical Inquiries & Contact:"
                        color: Theme.muted
                        font.pixelSize: 11
                    }
                    Text {
                        text: "sobahramisamani@gmail.com"
                        color: Theme.accent
                        font.pixelSize: 11
                        font.weight: Font.DemiBold
                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: Qt.openUrlExternally("mailto:sobahramisamani@gmail.com?subject=HEMOGLYPH%20Clinical%20Inquiry")
                        }
                    }
                }

                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: "Copyright © 2024–2026 Sobhan Bahrami. All rights reserved."
                    color: Theme.muted
                    font.pixelSize: 10
                    opacity: 0.7
                }
            }
        }
    }

    // ================================================================
    //  COMPONENTS
    // ================================================================

    component StatCard: HgCard {
        id: statCard
        required property string icon
        required property int number
        required property string label
        required property color accent
        property bool loading: false

        implicitHeight: 110

        ColumnLayout {
            anchors.centerIn: parent
            spacing: 4

            Text {
                Layout.alignment: Qt.AlignHCenter
                text: statCard.icon
                font.pixelSize: 26
            }

            Text {
                Layout.alignment: Qt.AlignHCenter
                text: statCard.loading ? "…" : statCard.number.toLocaleString()
                color: statCard.loading ? Theme.muted : statCard.accent
                font.pixelSize: 28
                font.weight: Font.Bold

                // Count-up animation
                Behavior on text {
                    enabled: !statCard.loading
                }
            }

            Text {
                Layout.alignment: Qt.AlignHCenter
                text: statCard.label
                color: Theme.muted
                font.pixelSize: 10
                font.weight: Font.DemiBold
            }
        }

        // Subtle top accent line
        Rectangle {
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.margins: 1
            height: 3
            radius: 2
            color: statCard.accent
            opacity: 0.6
        }
    }

    component CapabilityCard: HgCard {
        id: capCard
        required property string icon
        required property string title
        required property string desc
        signal clicked()

        implicitHeight: 150
        interactive: true

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 18
            spacing: 8

            RowLayout {
                Layout.fillWidth: true
                spacing: 10

                Rectangle {
                    width: 38; height: 38; radius: 12
                    color: Theme.surfaceAlt
                    border.color: Theme.border
                    Text { anchors.centerIn: parent; text: capCard.icon; font.pixelSize: 18 }
                }

                Text {
                    text: capCard.title
                    color: Theme.text
                    font.pixelSize: 14
                    font.weight: Font.DemiBold
                    Layout.fillWidth: true
                    elide: Text.ElideRight
                }

                Text {
                    text: "→"
                    color: Theme.accent
                    font.pixelSize: 16
                    opacity: capCard.hovered ? 1 : 0.3
                    Behavior on opacity { NumberAnimation { duration: 150 } }
                }
            }

            Text {
                Layout.fillWidth: true
                text: capCard.desc
                color: Theme.muted
                font.pixelSize: 11
                wrapMode: Text.Wrap
                lineHeight: 1.35
                Layout.fillHeight: true
            }
        }

        MouseArea {
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            onClicked: capCard.clicked()
        }
    }
}
