
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"
import ".."

HgCard {
    id: root
    implicitHeight: body.implicitHeight + 30

    // ================= public API (backward compatible) =================
    property alias ageText: ageField.text
    property alias sexIndex: sexBox.currentIndex
    property alias weightText: weightField.text
    property alias heightText: heightField.text

    function contextMap() {
        var map = {}
        if (ageField.text.length)
            map["age_years"] = Number(ageField.text)

        // Only send a sex once the clinician has actually chosen one.
        if (sexBox.currentIndex === 1)
            map["sex_at_birth"] = "female"
        else if (sexBox.currentIndex === 2)
            map["sex_at_birth"] = "male"

        if (weightField.text.length)
            map["weight_kg"] = Number(weightField.text)
        if (heightField.text.length)
            map["height_cm"] = Number(heightField.text)

        // ✅ Fasting: فقط وقتی مشخص است ارسال شود (Unknown => حذف => موتور آن را missing می‌شمارد)
        if (fastingBox.currentIndex === 0)
            map["fasting"] = true
        else if (fastingBox.currentIndex === 1)
            map["fasting"] = false

        // ✅ Pregnant: همین منطق
        if (pregnantBox.currentIndex === 0)
            map["pregnant"] = false
        else if (pregnantBox.currentIndex === 1)
            map["pregnant"] = true

        return map
    }

    // ✅ فرم همیشه خالی شروع می‌شود.
    // این ابزار دست پزشک است، نه دفترچه‌ی سلامت شخصی: هر تحلیل مربوط به
    // بیماری است که روبه‌روی اوست، نه صاحب حساب کاربری. پیش‌پرکردن از
    // پروفایل باعث می‌شد سن و جنس یک بیمار روی برگه‌ی بیمار بعدی بنشیند
    // بی‌آنکه کسی متوجه شود.
    function reset() {
        ageField.text = ""
        sexBox.currentIndex = 0
        weightField.text = ""
        heightField.text = ""
        fastingBox.currentIndex = 0
        pregnantBox.currentIndex = 0
    }

    // ================= body =================
    ColumnLayout {
        id: body
        anchors.fill: parent
        anchors.margins: 16
        spacing: 12

        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            Text { text: "CLINICAL CONTEXT"; color: Theme.muted; font.pixelSize: 10; font.bold: true; font.letterSpacing: 1.5 }
            Item { Layout.fillWidth: true }
            Text { text: "Auto-filled from your profile"; color: Theme.muted; font.pixelSize: 9 }
            ToolButton {
                id: refillBtn
                text: "↺"
                ToolTip.visible: hovered
                ToolTip.text: "Re-fill from profile"
                onClicked: root.reset()
                contentItem: Text {
                    text: refillBtn.text
                    color: Theme.accent
                    font.pixelSize: 15
                    horizontalAlignment: Text.AlignHCenter
                }
                background: Rectangle {
                    color: refillBtn.hovered ? Theme.surfaceAlt : "transparent"
                    radius: 8
                }
            }
        }

        GridLayout {
            Layout.fillWidth: true
            columns: 4
            columnSpacing: 12
            rowSpacing: 10

            ColumnLayout {
                spacing: 4
                Text { text: "Age (years)"; color: Theme.muted; font.pixelSize: 9 }
                HgField {
                    id: ageField
                    Layout.fillWidth: true
                    placeholderText: "e.g. 58"
                    validator: DoubleValidator { bottom: 0; top: 120 }
                }
            }

            ColumnLayout {
                spacing: 4
                Text { text: "Sex"; color: Theme.muted; font.pixelSize: 9 }
                HgCombo {
                    id: sexBox
                    Layout.fillWidth: true
                    // "Select…" first so an untouched form never asserts a
                    // sex. Sex drives reference ranges and several risk
                    // models, so guessing it is worse than omitting it.
                    model: ["Select…", "Female", "Male"]
                }
            }

            ColumnLayout {
                spacing: 4
                Text { text: "Weight (kg)"; color: Theme.muted; font.pixelSize: 9 }
                HgField {
                    id: weightField
                    Layout.fillWidth: true
                    placeholderText: "e.g. 72"
                    validator: DoubleValidator { bottom: 0; top: 500 }
                }
            }

            ColumnLayout {
                spacing: 4
                Text { text: "Height (cm)"; color: Theme.muted; font.pixelSize: 9 }
                HgField {
                    id: heightField
                    Layout.fillWidth: true
                    placeholderText: "e.g. 172"
                    validator: DoubleValidator { bottom: 0; top: 280 }
                }
            }

            ColumnLayout {
                spacing: 4
                Text { text: "Fasting"; color: Theme.muted; font.pixelSize: 9 }
                HgCombo {
                    id: fastingBox
                    Layout.fillWidth: true
                    model: ["Fasting", "Non-fasting", "Unknown"]
                }
            }

            ColumnLayout {
                spacing: 4
                Text { text: "Pregnant"; color: Theme.muted; font.pixelSize: 9 }
                HgCombo {
                    id: pregnantBox
                    Layout.fillWidth: true
                    model: ["No", "Yes", "Unknown"]
                }
            }
        }
    }

    Component.onCompleted: root.reset()

    // ================= ComboBox استایل‌دار و خودکفا =================
    // ارتفاع ۴۶ (هم‌اندازه HgField)، متن وسط‌چین بدون بریدگی،
    // فلش متحرک و لیست بازشوی هماهنگ با تم.
    component HgCombo: ComboBox {
        id: combo
        implicitHeight: 46
        leftPadding: 14
        rightPadding: 34
        font.family: Theme.fontFamily
        font.pixelSize: 13

        // متن داخل دکمه — کاملاً وسط‌چین، هرگز بریده نمی‌شود
        contentItem: Text {
            leftPadding: 0
            rightPadding: 0
            text: combo.displayText
            font: combo.font
            color: Theme.text
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }

        // بدنه دکمه
        background: Rectangle {
            implicitHeight: 46
            radius: 12
            color: combo.pressed || combo.hovered ? Theme.surfaceAlt : Theme.surface
            border.color: combo.activeFocus || combo.pressed ? Theme.accent : Theme.border
            border.width: combo.activeFocus ? 1.5 : 1
            Behavior on border.color { ColorAnimation { duration: 120 } }
            Behavior on color { ColorAnimation { duration: 120 } }
        }

        // فلش کوچک با انیمیشن چرخش
        indicator: Item {
            implicitWidth: 30
            implicitHeight: combo.height
            anchors.right: parent.right
            Text {
                anchors.centerIn: parent
                text: "▾"
                font.pixelSize: 11
                color: combo.activeFocus ? Theme.accent : Theme.muted
                rotation: combo.pressed ? -180 : 0
                Behavior on rotation { NumberAnimation { duration: 140 } }
            }
        }

        // لیست بازشو — هماهنگ با تم روشن/تاریک
        popup: Popup {
            y: combo.height + 4
            width: combo.width
            implicitHeight: Math.min(contentItem.implicitHeight + 16, 300)
            padding: 8
            background: Rectangle {
                radius: 12
                color: Theme.surface
                border.color: Theme.border
            }
            contentItem: ListView {
                clip: true
                implicitHeight: contentHeight
                model: combo.popup.visible ? combo.delegateModel : null
                currentIndex: combo.highlightedIndex
                ScrollIndicator.vertical: ScrollIndicator {}
            }
        }

        // آیتم‌های لیست
        delegate: ItemDelegate {
            id: opt
            width: ListView.view ? ListView.view.width : combo.width
            implicitHeight: 40
            hoverEnabled: true
            highlighted: combo.highlightedIndex === index
            contentItem: Text {
                leftPadding: 10
                rightPadding: 10
                verticalAlignment: Text.AlignVCenter
                elide: Text.ElideRight
                font: combo.font
                color: opt.highlighted ? Theme.text : Theme.muted
                text: modelData !== undefined && modelData !== null ? String(modelData) : ""
            }
            background: Rectangle {
                radius: 9
                color: opt.highlighted || opt.hovered ? Theme.surfaceAlt : "transparent"
            }
        }
    }
}

