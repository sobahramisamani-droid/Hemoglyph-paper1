import QtQuick
import QtQuick.Controls
import ".."

ComboBox {
    id: control
    implicitHeight: 42
    leftPadding: 14
    rightPadding: 36
    font.family: Theme.fontFamily
    font.pixelSize: 13

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
        radius: 12
        color: control.pressed || control.hovered ? Theme.surfaceAlt : Theme.surface
        border.color: control.activeFocus || control.pressed ? Theme.accent : Theme.border
        border.width: control.activeFocus ? 1.5 : 1
        Behavior on border.color { ColorAnimation { duration: 150 } }
        Behavior on color { ColorAnimation { duration: 150 } }
    }

    indicator: Item {
        implicitWidth: 28
        implicitHeight: control.height
        anchors.right: parent.right
        Text {
            anchors.centerIn: parent
            text: "▾"
            font.pixelSize: 12
            color: control.activeFocus ? Theme.accent : Theme.muted
            rotation: control.pressed ? -180 : 0
            Behavior on rotation { NumberAnimation { duration: 200; easing.type: Easing.OutBack } }
        }
    }

    popup: Popup {
        y: control.height + 6
        width: control.width
        implicitHeight: Math.min(contentItem.implicitHeight + 16, 300)
        padding: 8
        background: Rectangle {
            radius: 12
            color: Theme.surface
            border.color: Theme.border
            layer.enabled: true
            layer.effect: Item { /* Shadow placeholder */ }
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
        id: optionItem
        width: ListView.view ? ListView.view.width : control.width
        implicitHeight: 40
        highlighted: control.highlightedIndex === index
        contentItem: Text {
            leftPadding: 10
            rightPadding: 10
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
            font: control.font
            color: optionItem.highlighted ? Theme.text : Theme.muted
            text: control.textRole && typeof modelData === "object" && modelData !== null
                  ? (modelData[control.textRole] !== undefined ? String(modelData[control.textRole]) : "")
                  : (modelData !== undefined && modelData !== null ? String(modelData) : "")
        }
        background: Rectangle {
            radius: 8
            color: optionItem.highlighted || optionItem.hovered ? Theme.surfaceAlt : "transparent"
        }
    }
}