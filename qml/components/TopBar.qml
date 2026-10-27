import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."

Rectangle {
    id: root
    height: 72
    color: Theme.background
    property string title: "Workspace"
    Rectangle { anchors.left: parent.left; anchors.right: parent.right; anchors.bottom: parent.bottom; height: 1; color: Theme.border }
    Rectangle { anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.bottom; height: 8; z: 5
        gradient: Gradient { GradientStop { position: 0; color: Theme.shadowSoft } GradientStop { position: 1; color: "transparent" } } }

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 28
        anchors.rightMargin: 28

        Text {
            text: root.title
            color: Theme.text
            font.family: Theme.fontFamily
            font.pixelSize: 16
            font.weight: Font.DemiBold
            Layout.preferredWidth: 200
        }

        // Live Sentinel Internet Link Indicator
        Rectangle {
            height: 28
            radius: 14
            color: (backend && backend.sentinelOnline) ? "#1510B981" : "#1094A3B8"
            border.color: (backend && backend.sentinelOnline) ? "#3510B981" : "#2094A3B8"
            border.width: 1
            implicitWidth: statusRow.implicitWidth + 20

            RowLayout {
                id: statusRow
                anchors.centerIn: parent
                spacing: 6

                Rectangle {
                    width: 7; height: 7; radius: 3.5
                    color: (backend && backend.sentinelOnline) ? "#10B981" : "#94A3B8"

                    SequentialAnimation on opacity {
                        loops: Animation.Infinite
                        running: backend ? backend.sentinelOnline : false
                        NumberAnimation { from: 1.0; to: 0.3; duration: 800 }
                        NumberAnimation { from: 0.3; to: 1.0; duration: 800 }
                    }
                }

                Text {
                    text: (backend && backend.sentinelOnline) ? "ONLINE · SENTINEL LINKED" : "OFFLINE · LOCAL CDS"
                    color: (backend && backend.sentinelOnline) ? "#34D399" : "#94A3B8"
                    font.pixelSize: 10
                    font.weight: Font.Bold
                    font.letterSpacing: 0.6
                }
            }
        }

        Item {
            Layout.fillWidth: true
        }

        TextField {
            id: search
            Layout.preferredWidth: 360
            implicitHeight: 42
            placeholderText: "Search analyses, features, diseases…"
            color: Theme.text
            placeholderTextColor: Theme.muted
            leftPadding: 42
            rightPadding: topSearchClearBtn.visible ? 36 : 14
            horizontalAlignment: TextInput.AlignLeft
            verticalAlignment: TextInput.AlignVCenter
            font.family: Theme.fontFamily
            font.pixelSize: 13
            onTextChanged: searchDelay.restart()

            ToolButton {
                id: topSearchClearBtn
                visible: search.text.length > 0
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
                    color: topSearchClearBtn.hovered ? (Theme.dark ? "#334155" : "#E2E8F0") : "transparent"
                }
                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    acceptedButtons: Qt.NoButton
                }
                onClicked: {
                    search.text = ""
                    searchPopup.close()
                }
            }

            Timer {
                id: searchDelay
                interval: 180
                repeat: false

                onTriggered: {
                    backend.globalSearch(search.text)

                    if (search.text.length)
                        searchPopup.open()
                    else
                        searchPopup.close()
                }
            }

            background: Rectangle {
                radius: 13
                color: Theme.surface
                border.color: search.activeFocus
                              ? Theme.accent
                              : Theme.border
            }

            Text {
                anchors.left: parent.left
                anchors.leftMargin: 15
                anchors.verticalCenter: parent.verticalCenter
                text: "⌕"
                color: Theme.muted
                font.pixelSize: 20
            }

            Popup {
                id: searchPopup

                y: search.height + 7
                width: search.width
                height: Math.min(
                    380,
                    (backend && backend.globalSearchRows ? backend.globalSearchRows.length : 0) * 58 + 14
                )

                padding: 7

                closePolicy:
                    Popup.CloseOnEscape |
                    Popup.CloseOnPressOutside

                background: Rectangle {
                    color: Theme.surface
                    border.color: Theme.border
                    radius: 14
                }

                contentItem: ListView {
                    model: backend ? backend.globalSearchRows : []
                    clip: true

                    delegate: ItemDelegate {
                        id: searchResultDelegate

                        required property string title
                        required property string subtitle
                        required property string kind
                        required property string itemId

                        width: ListView.view.width
                        height: 58

                        onClicked: {
                            backend.openSearchResult(
                                kind,
                                itemId
                            )
                            searchPopup.close()
                        }

                        contentItem: Column {
                            spacing: 2

                            Text {
                                text: title || ""
                                color: Theme.text
                                font.pixelSize: 13
                                font.weight: Font.DemiBold
                                elide: Text.ElideRight
                                width: parent.width
                            }

                            Text {
                                text: (kind || "")
                                      + " · "
                                      + (subtitle || "")
                                color: Theme.muted
                                font.pixelSize: 10
                                elide: Text.ElideRight
                                width: parent.width
                            }
                        }

                        background: Rectangle {
                            color: searchResultDelegate.hovered
                                   ? Theme.surfaceAlt
                                   : "transparent"
                            radius: 9
                        }
                    }
                }
            }
        }

        Rectangle {
            width: 38
            height: 38
            radius: 12
            color: Theme.surface
            border.color: Theme.border

            Text {
                anchors.centerIn: parent
                text: "?"
                color: Theme.muted
                font.bold: true
            }
        }
    }
}
