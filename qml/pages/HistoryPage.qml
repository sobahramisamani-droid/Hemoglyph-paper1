import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"
import ".."

Item {
    id: root

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 30
        spacing: 16

        // Header
        RowLayout {
            Layout.fillWidth: true
            spacing: 12
            ColumnLayout {
                spacing: 3
                Text { text: "Analysis History"; color: Theme.text; font.pixelSize: 26; font.bold: true }
                Text { text: (backend && backend.historyRows ? backend.historyRows.length : 0) + " saved clinical analyses in database"; color: Theme.muted; font.pixelSize: 12 }
            }
            Item { Layout.fillWidth: true }
            HgButton {
                text: "🔄 Refresh"; implicitHeight: 36
                onClicked: if (backend) backend.load_history()
            }
            HgButton {
                text: "+ New Analysis"; primary: true; implicitHeight: 36
                onClicked: if (backend) backend.navigate("newAnalysis")
            }
        }

        // List of history items
        ListView {
            id: historyList
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: (backend && backend.historyRows ? backend.historyRows.length : 0) > 0
            model: backend ? backend.historyRows : []
            clip: true
            spacing: 10
            ScrollBar.vertical: ScrollBar {
                id: histVbar
                policy: historyList.contentHeight > historyList.height ? ScrollBar.AlwaysOn : ScrollBar.AsNeeded
                width: 8
                contentItem: Rectangle {
                    implicitWidth: 8; radius: 4
                    color: Theme.dark
                        ? (histVbar.pressed ? "#94A3B8" : (histVbar.hovered ? "#64748B" : "#475569"))
                        : (histVbar.pressed ? "#475467" : (histVbar.hovered ? "#98A2B3" : "#CBD5E1"))
                }
            }

            delegate: HgCard {
                id: cardItem
                required property var modelData
                width: ListView.view ? ListView.view.width : 0
                implicitHeight: 82
                interactive: true

                // Make the entire card body clickable to open history
                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    hoverEnabled: true
                    onClicked: backend.openHistory(parseInt(modelData.testId, 10))
                }

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 14

                    // Status / Icon Badge
                    Rectangle {
                        width: 44; height: 44; radius: 22
                        color: Theme.surfaceAlt
                        border.color: Theme.border
                        Text {
                            anchors.centerIn: parent
                            text: "📊"
                            font.pixelSize: 18
                        }
                    }

                    // Title & Metadata
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4

                        Text {
                            text: modelData.title || "Laboratory Analysis"
                            color: Theme.text
                            font.pixelSize: 14
                            font.weight: Font.DemiBold
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                        }

                        RowLayout {
                            spacing: 8
                            Rectangle {
                                implicitWidth: dateBadge.implicitWidth + 12; height: 20; radius: 10
                                color: Theme.surfaceAlt; border.color: Theme.border
                                Text {
                                    id: dateBadge; anchors.centerIn: parent
                                    text: "📅 " + (modelData.date || "Unknown date")
                                    color: Theme.muted; font.pixelSize: 10; font.bold: true
                                }
                            }
                            Text {
                                text: modelData.subtitle ? "·  " + modelData.subtitle : ""
                                color: Theme.muted
                                font.pixelSize: 11
                                elide: Text.ElideRight
                                Layout.fillWidth: true
                            }
                        }
                    }

                    // Action Buttons (Explicit & High Contrast)
                    RowLayout {
                        spacing: 8
                        Layout.alignment: Qt.AlignVCenter

                        HgButton {
                            text: "Open Analysis →"
                            primary: true
                            implicitHeight: 38
                            leftPadding: 16
                            rightPadding: 16
                            onClicked: backend.openHistory(parseInt(modelData.testId, 10))
                        }

                        HgButton {
                            text: "Delete"
                            danger: true
                            implicitHeight: 38
                            leftPadding: 14
                            rightPadding: 14
                            onClicked: backend.deleteHistory(parseInt(modelData.testId, 10))
                        }
                    }
                }
            }
        }

        // Empty state
        HgCard {
            visible: (backend && backend.historyRows ? backend.historyRows.length : 0) === 0
            Layout.fillWidth: true
            Layout.fillHeight: true

            ColumnLayout {
                anchors.centerIn: parent
                spacing: 12

                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: "📂"
                    font.pixelSize: 42
                    opacity: 0.6
                }
                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: "No Saved Analyses Found"
                    color: Theme.text
                    font.pixelSize: 18
                    font.bold: true
                }
                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: "Analyses you perform and save will appear here for longitudinal review."
                    color: Theme.muted
                    font.pixelSize: 13
                }
                HgButton {
                    Layout.alignment: Qt.AlignHCenter
                    text: "Start a New Analysis"
                    primary: true
                    implicitHeight: 40
                    onClicked: backend.navigate("newAnalysis")
                }
            }
        }
    }

    Component.onCompleted: backend.load_history()
}
