import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"
import ".."
Flickable {
    id: root
    contentWidth: width
    contentHeight: content.implicitHeight + 80
    clip: true
    ScrollBar.vertical: ScrollBar {}

    ColumnLayout {
        id: content
        width: Math.min(root.width - 80, 1080)
        anchors.horizontalCenter: parent.horizontalCenter
        y: 55
        spacing: 20

        Text { text: "NEW ANALYSIS"; color: Theme.accent; font.pixelSize: 11; font.bold: true; font.letterSpacing: 2 }
        Text { text: "Understand your lab report."; color: Theme.text; font.pixelSize: 42; font.weight: Font.Bold; font.letterSpacing: -1.5 }
        Text { text: "Choose how you want to add results. Nothing is interpreted until you review and confirm every value."; color: Theme.muted; font.pixelSize: 15; wrapMode: Text.Wrap; Layout.maximumWidth: 760 }

        Item { height: 8 }

        RowLayout {
            Layout.fillWidth: true; spacing: 20
            ChoiceCard {
                Layout.fillWidth: true; iconText: "⌁"; title: "Upload laboratory report"
                description: "Extract values from an image or PDF, review every mapping, then run the analysis."
                badge: "OCR + HUMAN REVIEW"
                onChosen: backend.navigate("upload")
            }
            ChoiceCard {
                Layout.fillWidth: true; iconText: "✎"; title: "Enter results manually"
                description: "Search the " + (backend ? backend.featureCount : 2045) + "-feature registry and enter only the measurements you have."
                badge: "CANONICAL FEATURE IDS"
                onChosen: backend.navigate("manual")
            }
        }

        RowLayout {
            Layout.fillWidth: true; spacing: 14; Layout.topMargin: 12
            StatCard { Layout.fillWidth: true; number: String(backend ? backend.featureCount : 2045); label: "Laboratory features" }
            StatCard { Layout.fillWidth: true; number: String(backend ? backend.diseaseCount : 6702); label: "Clinical concepts" }
            StatCard { Layout.fillWidth: true; number: String(backend ? backend.ruleCount : 33170); label: "Research rules" }
        }

        Rectangle {
            Layout.fillWidth: true; implicitHeight: 62; radius: 14
            color: "#FFFAEB"; border.color: "#FEC84B"
            Text { anchors.fill: parent; anchors.margins: 16; verticalAlignment: Text.AlignVCenter; wrapMode: Text.Wrap; color: "#8A6100"; font.pixelSize: 12; text: "HEMOGLYPH identifies laboratory criteria and compatible patterns. It does not diagnose disease or prescribe treatment." }
        }
    }

    component ChoiceCard: HgCard {
        id: card
        signal chosen()
        required property string iconText
        required property string title
        required property string description
        required property string badge
        implicitHeight: 245

        ColumnLayout {
            anchors.fill: parent; anchors.margins: 24; spacing: 12
            Rectangle {
                width: 54; height: 54; radius: 17; color: "#1323BFE5"; border.color: "#2023BFE5"
                Text { anchors.centerIn: parent; text: card.iconText; color: Theme.accent; font.pixelSize: 25 }
            }
            Text { text: card.title; color: Theme.text; font.pixelSize: 19; font.weight: Font.DemiBold }
            Text { text: card.description; color: Theme.muted; font.pixelSize: 13; wrapMode: Text.Wrap; Layout.fillWidth: true }
            Item { Layout.fillHeight: true }
            RowLayout {
                Rectangle { implicitWidth: badgeText.implicitWidth + 18; height: 26; radius: 13; color: "#1123BFE5"; Text { id: badgeText; anchors.centerIn: parent; text: card.badge; color: "#1097B5"; font.pixelSize: 9; font.bold: true; font.letterSpacing: 1 } }
                Item { Layout.fillWidth: true }
                Text { text: "→"; color: Theme.violet; font.pixelSize: 21 }
            }
        }
        MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: card.chosen() }
    }

    component StatCard: HgCard {
        required property string number
        required property string label
        implicitHeight: 90
        Column { anchors.centerIn: parent; spacing: 3
            Text { anchors.horizontalCenter: parent.horizontalCenter; text: number; color: Theme.text; font.pixelSize: 26; font.bold: true }
            Text { anchors.horizontalCenter: parent.horizontalCenter; text: label; color: Theme.muted; font.pixelSize: 11 }
        }
    }
}