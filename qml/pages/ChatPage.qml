import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"
import ".."

Item {
    id: root

    Flickable {
        anchors.fill: parent
        contentWidth: width
        contentHeight: contentCol.implicitHeight + 80
        clip: true
        boundsBehavior: Flickable.StopAtBounds

        ScrollBar.vertical: ScrollBar {
            id: vbar
            width: 8
            anchors.right: parent.right
            anchors.rightMargin: 4
        }

        ColumnLayout {
            id: contentCol
            width: Math.min(root.width - 64, 880)
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: parent.top
            anchors.topMargin: 36
            spacing: 24

            // Top Header
            RowLayout {
                Layout.fillWidth: true
                spacing: 12

                ColumnLayout {
                    spacing: 4
                    Text {
                        text: "Clinical AI Assistant"
                        color: Theme.text
                        font.family: Theme.fontFamily
                        font.pixelSize: 24
                        font.weight: Font.Bold
                    }
                    Text {
                        text: "Local on-device reasoning and interactive clinical explanations"
                        color: Theme.muted
                        font.family: Theme.fontFamily
                        font.pixelSize: 12
                    }
                }

                Item { Layout.fillWidth: true }

                Rectangle {
                    implicitWidth: devBadge.implicitWidth + 24
                    implicitHeight: 32
                    radius: 16
                    color: Theme.dark ? "#172554" : "#EFF6FF"
                    border.color: Theme.dark ? "#1E40AF" : "#BFDBFE"
                    border.width: 1

                    RowLayout {
                        anchors.centerIn: parent
                        spacing: 8
                        Rectangle {
                            width: 8
                            height: 8
                            radius: 4
                            color: "#38BDF8"
                            SequentialAnimation on opacity {
                                loops: Animation.Infinite
                                NumberAnimation { from: 1.0; to: 0.3; duration: 900 }
                                NumberAnimation { from: 0.3; to: 1.0; duration: 900 }
                            }
                        }
                        Text {
                            id: devBadge
                            text: "UNDER DEVELOPMENT"
                            color: Theme.dark ? "#93C5FD" : "#1D4ED8"
                            font.pixelSize: 10
                            font.weight: Font.Bold
                            font.letterSpacing: 1
                        }
                    }
                }
            }

            // Main Hero Notice Card
            HgCard {
                Layout.fillWidth: true
                implicitHeight: cardInner.implicitHeight + 48

                ColumnLayout {
                    id: cardInner
                    anchors.fill: parent
                    anchors.margins: 28
                    spacing: 20

                    // Emblem & Icon
                    Rectangle {
                        Layout.alignment: Qt.AlignHCenter
                        width: 72
                        height: 72
                        radius: 36
                        color: Theme.dark ? "#1E293B" : "#F1F5F9"
                        border.color: Theme.dark ? "#334155" : "#E2E8F0"
                        border.width: 1.5

                        Text {
                            anchors.centerIn: parent
                            text: "🤖"
                            font.pixelSize: 32
                        }
                    }

                    // Notice Titles
                    ColumnLayout {
                        Layout.alignment: Qt.AlignHCenter
                        spacing: 8

                        Text {
                            Layout.alignment: Qt.AlignHCenter
                            text: "AI Assistant Module is Currently Under Development (v1.3.1)"
                            color: Theme.text
                            font.family: Theme.fontFamily
                            font.pixelSize: 18
                            font.weight: Font.Bold
                            horizontalAlignment: Text.AlignHCenter
                        }

                        Text {
                            Layout.alignment: Qt.AlignHCenter
                            Layout.preferredWidth: Math.min(parent.width, 680)
                            wrapMode: Text.Wrap
                            horizontalAlignment: Text.AlignHCenter
                            lineHeight: 1.4
                            text: "The local on-device clinical language model (LLM) is currently under active development and disabled in Release v1.3.1 to ensure zero runtime dependency and high token performance across all client hardware.\n\nAll core diagnostic and clinical reasoning engines — including " + (backend && backend.ruleCount > 0 ? backend.ruleCount.toLocaleString() : "33,230") + " evidence rules across " + (backend && backend.sourceCount > 0 ? backend.sourceCount.toLocaleString() : "747") + " guideline sources, " + (backend && backend.featureCount > 0 ? backend.featureCount.toLocaleString() : "2,045") + " laboratory features, and 100 risk prediction models — remain fully active, grounded, and operational."
                            color: Theme.muted
                            font.family: Theme.fontFamily
                            font.pixelSize: 12
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        height: 1
                        color: Theme.border
                    }

                    // Active Clinical Features Grid
                    Text {
                        text: "ACTIVE MODULES IN THIS VERSION"
                        color: Theme.accent
                        font.pixelSize: 10
                        font.weight: Font.Bold
                        font.letterSpacing: 1.2
                    }

                    GridLayout {
                        Layout.fillWidth: true
                        columns: root.width > 700 ? 3 : 1
                        rowSpacing: 12
                        columnSpacing: 12

                        // Card 1: Rules
                        Rectangle {
                            Layout.fillWidth: true
                            implicitHeight: 90
                            radius: 12
                            color: Theme.surfaceAlt
                            border.color: Theme.border

                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 14
                                spacing: 4
                                RowLayout {
                                    spacing: 8
                                    Text { text: "📐"; font.pixelSize: 12 }
                                    Text {
                                        text: (backend && backend.ruleCount > 0 ? backend.ruleCount.toLocaleString() : "33,230") + " Research Rules"
                                        color: Theme.text
                                        font.weight: Font.DemiBold
                                        font.pixelSize: 12
                                    }
                                }
                                Text {
                                    text: (backend && backend.sourceCount > 0 ? backend.sourceCount.toLocaleString() : "781") + " guideline sources across " + (backend && backend.diseaseCount > 0 ? backend.diseaseCount.toLocaleString() : "6,702") + " clinical concepts evaluated automatically."
                                    color: Theme.muted; font.pixelSize: 10; wrapMode: Text.Wrap; Layout.fillWidth: true
                                }
                            }
                        }

                        // Card 2: Laboratory Features & Equations
                        Rectangle {
                            Layout.fillWidth: true
                            implicitHeight: 90
                            radius: 12
                            color: Theme.surfaceAlt
                            border.color: Theme.border

                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 14
                                spacing: 4
                                RowLayout {
                                    spacing: 8
                                    Text { text: "🔬"; font.pixelSize: 12 }
                                    Text {
                                        text: (backend && backend.featureCount > 0 ? backend.featureCount.toLocaleString() : "2,045") + " Laboratory Features"
                                        color: Theme.text
                                        font.weight: Font.DemiBold
                                        font.pixelSize: 12
                                    }
                                }
                                Text {
                                    text: "Pediatric & adult reference intervals, biomarker normalization, and 14+ derived equations."
                                    color: Theme.muted; font.pixelSize: 10; wrapMode: Text.Wrap; Layout.fillWidth: true
                                }
                            }
                        }

                        // Card 3: Risk Models
                        Rectangle {
                            Layout.fillWidth: true
                            implicitHeight: 90
                            radius: 12
                            color: Theme.surfaceAlt
                            border.color: Theme.border

                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 14
                                spacing: 4
                                RowLayout {
                                    spacing: 8
                                    Text { text: "📊"; font.pixelSize: 12 }
                                    Text { text: "100 Risk Models"; color: Theme.text; font.weight: Font.DemiBold; font.pixelSize: 12 }
                                }
                                Text {
                                    text: "ASCVD, FINDRISC, Framingham, and Caprini multi-year risk projections."
                                    color: Theme.muted; font.pixelSize: 10; wrapMode: Text.Wrap; Layout.fillWidth: true
                                }
                            }
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        height: 1
                        color: Theme.border
                    }

                    // Navigation Actions
                    RowLayout {
                        Layout.alignment: Qt.AlignHCenter
                        spacing: 12

                        HgButton {
                            text: "📊 View Clinical Results"
                            primary: true
                            implicitHeight: 40
                            leftPadding: 18
                            rightPadding: 18
                            onClicked: backend.navigate("results")
                        }

                        HgButton {
                            text: "◈ Explore Guidelines"
                            implicitHeight: 40
                            leftPadding: 16
                            rightPadding: 16
                            onClicked: backend.navigate("guidelines")
                        }

                        HgButton {
                            text: "📐 100 Risk Models"
                            implicitHeight: 40
                            leftPadding: 16
                            rightPadding: 16
                            onClicked: backend.navigate("riskmodels")
                        }
                    }
                }
            }
        }
    }
}
