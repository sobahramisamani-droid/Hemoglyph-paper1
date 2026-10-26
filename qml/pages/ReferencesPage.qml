import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"
import ".."

Item {
    id: root

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 34
        spacing: 16

        // =========================================================
        // HEADER
        // =========================================================
        ColumnLayout {
            spacing: 3
            Layout.fillWidth: true

            Text {
                text: "Evidence library"
                color: Theme.text
                font.family: Theme.fontFamily
                font.pixelSize: 30
                font.bold: true
            }

            Text {
                text: "Official guideline sources connected to the research rule registry"
                color: Theme.muted
                font.family: Theme.fontFamily
                font.pixelSize: 12
                wrapMode: Text.Wrap
                Layout.fillWidth: true
            }
        }

        // =========================================================
        // SEARCH
        // =========================================================
        TextField {
            id: searchField

            Layout.fillWidth: true
            implicitHeight: 44

            placeholderText: "Search ADA, kidney, diabetes, 2026…"

            color: Theme.text
            placeholderTextColor: Theme.muted

            selectByMouse: true
            horizontalAlignment: TextInput.AlignLeft
            verticalAlignment: TextInput.AlignVCenter
            leftPadding: 14
            rightPadding: refSearchClearBtn.visible ? 36 : 14
            font.family: Theme.fontFamily
            font.pixelSize: 13

            onTextChanged: {
                referenceSearchDelay.restart()
            }

            background: Rectangle {
                radius: 12
                color: Theme.surface
                border.color: searchField.activeFocus
                              ? Theme.accent
                              : Theme.border
            }

            ToolButton {
                id: refSearchClearBtn
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
                    color: refSearchClearBtn.hovered ? (Theme.dark ? "#334155" : "#E2E8F0") : "transparent"
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

        Timer {
            id: referenceSearchDelay

            interval: 180
            repeat: false

            onTriggered: {
                backend.searchReferences(searchField.text)
            }
        }

        // =========================================================
        // INFO BAR
        // =========================================================
        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            Rectangle {
                implicitWidth: badgeText.implicitWidth + 24
                height: 30
                radius: 15

                color: Theme.dark ? "#102A4C" : "#EFF8FF"
                border.color: Theme.dark ? "#1D4ED8" : "#B2DDFF"

                Text {
                    id: badgeText

                    anchors.centerIn: parent

                    text: (backend && backend.referenceRows ? backend.referenceRows.length : 0)
                          + " sources"

                    color: Theme.dark ? "#93C5FD" : "#175CD3"
                    font.pixelSize: 10
                    font.bold: true
                }
            }

            Item {
                Layout.fillWidth: true
            }

            Text {
                text: "Open links in your default browser"
                color: Theme.muted
                font.pixelSize: 10
            }
        }

        // =========================================================
        // EMPTY STATE
        // =========================================================
        HgCard {
            Layout.fillWidth: true
            Layout.fillHeight: true

            visible: (backend && backend.referenceRows ? backend.referenceRows.length : 0) === 0

            ColumnLayout {
                anchors.centerIn: parent
                spacing: 8

                Text {
                    Layout.alignment: Qt.AlignHCenter

                    text: "▣"
                    color: Theme.muted
                    font.pixelSize: 38
                }

                Text {
                    Layout.alignment: Qt.AlignHCenter

                    text: searchField.text.length > 0
                          ? "No matching references"
                          : "No guideline references available"

                    color: Theme.text
                    font.pixelSize: 16
                    font.weight: Font.DemiBold
                }

                Text {
                    Layout.alignment: Qt.AlignHCenter
                    Layout.maximumWidth: 500

                    text: searchField.text.length > 0
                          ? "Try another organization, title, topic, or year."
                          : "The registry currently contains no reference sources."

                    color: Theme.muted
                    font.pixelSize: 11
                    wrapMode: Text.Wrap
                    horizontalAlignment: Text.AlignHCenter
                }
            }
        }

        // =========================================================
        // REFERENCE GRID
        // =========================================================
        GridView {
            id: referenceGrid

            Layout.fillWidth: true
            Layout.fillHeight: true

            visible: (backend && backend.referenceRows ? backend.referenceRows.length : 0) > 0

            model: backend ? backend.referenceRows : []

            clip: true

            cellWidth: width >= 1050
                       ? width / 3
                       : width >= 700
                       ? width / 2
                       : width

            cellHeight: 220

            ScrollBar.vertical: ScrollBar {
                id: refVbar
                policy: referenceGrid.contentHeight > referenceGrid.height ? ScrollBar.AlwaysOn : ScrollBar.AsNeeded
                width: 8
                contentItem: Rectangle {
                    implicitWidth: 8; radius: 4
                    color: Theme.dark
                        ? (refVbar.pressed ? "#94A3B8" : (refVbar.hovered ? "#64748B" : "#475569"))
                        : (refVbar.pressed ? "#475467" : (refVbar.hovered ? "#98A2B3" : "#CBD5E1"))
                }
            }

            delegate: Item {
                id: referenceDelegate

                // IMPORTANT:
                // referenceModel is a custom QAbstractListModel.
                // Do NOT use modelData here.
                required property string sourceId
                required property string organization
                required property string title
                required property string year
                required property string url
                required property string scope
                required property string accessed
                required property string evidenceStatus

                width: GridView.view.cellWidth
                height: GridView.view.cellHeight

                HgCard {
                    id: card

                    anchors.fill: parent
                    anchors.margins: 7

                    interactive: true

                    MouseArea {
                        anchors.fill: parent
                        cursorShape: (url && url.length > 0) ? Qt.PointingHandCursor : Qt.ArrowCursor
                        acceptedButtons: Qt.LeftButton
                        onClicked: {
                            if (url && url.length > 0)
                                Qt.openUrlExternally(url)
                        }
                    }

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 18
                        spacing: 8

                        // -------------------------------------------------
                        // Organization / source icon
                        // -------------------------------------------------
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 10

                            Rectangle {
                                width: 42
                                height: 42
                                radius: 13

                                color: "#1323BFE5"

                                Text {
                                    anchors.centerIn: parent

                                    text: "▣"

                                    color: Theme.accent
                                    font.pixelSize: 19
                                }
                            }

                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 2

                                Text {
                                    text: organization || "Unknown organization"

                                    color: Theme.text
                                    font.pixelSize: 14
                                    font.weight: Font.DemiBold

                                    elide: Text.ElideRight
                                    Layout.fillWidth: true
                                }

                                Text {
                                    text: {
                                        var parts = []

                                        if (year && year.length > 0)
                                            parts.push(year)

                                        if (sourceId && sourceId.length > 0)
                                            parts.push(sourceId)

                                        return parts.join(" · ")
                                    }

                                    color: Theme.muted
                                    font.pixelSize: 9

                                    elide: Text.ElideRight
                                    Layout.fillWidth: true
                                }
                            }
                        }

                        // -------------------------------------------------
                        // Title
                        // -------------------------------------------------
                        Text {
                            Layout.fillWidth: true

                            text: title || "Untitled reference"

                            color: Theme.text
                            font.pixelSize: 12
                            font.weight: Font.DemiBold

                            wrapMode: Text.Wrap
                            maximumLineCount: 3
                            elide: Text.ElideRight
                        }

                        Item {
                            Layout.fillHeight: true
                        }

                        // -------------------------------------------------
                        // Evidence status
                        // -------------------------------------------------
                        Rectangle {
                            visible: evidenceStatus
                                     && evidenceStatus.length > 0

                            Layout.fillWidth: true
                            implicitHeight: 26

                            radius: 13

                            color: "#F8F9FC"
                            border.color: Theme.border

                            Text {
                                anchors.fill: parent
                                anchors.leftMargin: 10
                                anchors.rightMargin: 10

                                verticalAlignment: Text.AlignVCenter

                                text: evidenceStatus

                                color: Theme.muted
                                font.pixelSize: 9

                                elide: Text.ElideRight
                            }
                        }

                        // -------------------------------------------------
                        // Scope / accessed date
                        // -------------------------------------------------
                        Text {
                            Layout.fillWidth: true

                            text: {
                                var result = scope || ""

                                if (accessed && accessed.length > 0) {
                                    if (result.length > 0)
                                        result += "  ·  "

                                    result += "Accessed " + accessed
                                }

                                return result || "Reference metadata unavailable"
                            }

                            color: Theme.violet
                            font.pixelSize: 9

                            elide: Text.ElideRight
                        }

                        // -------------------------------------------------
                        // Open link
                        // -------------------------------------------------
                        RowLayout {
                            Layout.fillWidth: true

                            Item {
                                Layout.fillWidth: true
                            }

                            HgButton {
                                text: url && url.length > 0
                                      ? "Open ↗"
                                      : "No link"

                                enabled: url && url.length > 0

                                onClicked: {
                                    if (url && url.length > 0)
                                        Qt.openUrlExternally(url)
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // =============================================================
    // INITIAL LOAD
    // =============================================================
    Component.onCompleted: {
        backend.searchReferences("")
    }
}