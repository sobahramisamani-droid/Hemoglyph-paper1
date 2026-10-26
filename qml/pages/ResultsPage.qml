import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"
import ".."

Flickable {
    id: root
    contentWidth: width
    contentHeight: content.implicitHeight + 100
    clip: true
    boundsBehavior: Flickable.StopAtBounds

    // ================================================================
    // 🌟 HIGH-CONTRAST SCROLLBAR (Visible in Dark & Light modes)
    // ================================================================
    ScrollBar.vertical: ScrollBar {
        id: vbar
        policy: root.contentHeight > root.height ? ScrollBar.AlwaysOn : ScrollBar.AsNeeded
        width: 10
        anchors.right: parent.right
        anchors.rightMargin: 3
        contentItem: Rectangle {
            implicitWidth: 10
            radius: 5
            color: Theme.dark
                ? (vbar.pressed ? "#94A3B8" : (vbar.hovered ? "#64748B" : "#475569"))
                : (vbar.pressed ? "#475467" : (vbar.hovered ? "#98A2B3" : "#CBD5E1"))
        }
        background: Rectangle {
            color: Theme.dark ? "#0F172A" : "#F8FAFC"
            radius: 5
            opacity: 0.5
        }
    }

    // ================================================================
    // 🖱️ UNIVERSAL MOUSE WHEEL SCROLLING
    // ================================================================
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

    // ================================================================
    // State
    // ================================================================
    property string filterText: ""
    property string clinicalFilterText: ""
    property string riskFilterText: ""
    property bool summaryExpanded: true

    function countKind(kind) {
        var n = 0
        var rows = (backend && backend.clinicalRows) ? backend.clinicalRows : []
        for (var i = 0; i < rows.length; i++)
            if (rows[i].kind === kind) n++
        return n
    }

    ColumnLayout {
        id: content
        width: Math.min(root.width - 60, 1340)
        anchors.horizontalCenter: parent.horizontalCenter
        y: 28
        spacing: 24

        // ============================================================
        // HEADER
        // ============================================================
        RowLayout {
            Layout.fillWidth: true; spacing: 14
            ColumnLayout {
                spacing: 4
                Text { text: "ANALYSIS COMPLETE"; color: Theme.success; font.pixelSize: 10; font.bold: true; font.letterSpacing: 2 }
                Text { text: "Your Laboratory Workspace"; color: Theme.text; font.pixelSize: 32; font.bold: true; font.letterSpacing: -0.5 }
                Text { text: "Measured values, calculated features, guideline-linked patterns, and validated scientific risk models."; color: Theme.muted; font.pixelSize: 13 }
            }
            Item { Layout.fillWidth: true }

            // 🌟 PROMINENT AI SUMMARY BUTTON IN HEADER (Disabled for this release)
            HgButton {
                id: goToAiSummaryBtn
                visible: false
                text: "💬 ارائه‌ی خلاصه و دستیار بالینی (AI Summary) →"
                primary: true
                implicitHeight: 40
                leftPadding: 18
                rightPadding: 18
                font.bold: true
                font.pixelSize: 13
                onClicked: backend.continueToChat()
            }

            Rectangle {
                width: 170; height: 38; radius: 19
                color: Theme.dark
                    ? ((backend && backend.urgentCount) ? "#381014" : "#082F1D")
                    : ((backend && backend.urgentCount) ? "#FEF3F2" : "#ECFDF3")
                border.color: Theme.dark
                    ? ((backend && backend.urgentCount) ? "#7A271A" : "#085D3A")
                    : ((backend && backend.urgentCount) ? "#FDA29B" : "#75E0A7")
                Text {
                    anchors.centerIn: parent
                    text: (backend && backend.urgentCount) ? "● Urgent review required" : "● Analysis ready"
                    color: Theme.dark
                        ? ((backend && backend.urgentCount) ? "#FCA5A5" : "#86EFAC")
                        : ((backend && backend.urgentCount) ? "#B42318" : "#067647")
                    font.pixelSize: 11; font.bold: true
                }
            }
        }

        // ============================================================
        // 🏥 MASTER CLINICAL DECISION SUPPORT & TRIAGE HUB (RTL)
        // ============================================================
        HgCard {
            Layout.fillWidth: true
            implicitHeight: triageHubCol.implicitHeight + 40
            color: Theme.surface
            border.color: Theme.dark
                ? (((backend ? backend.tier1Count : 0) > 0) ? "#991B1B" : (((backend ? backend.tier2Count : 0) > 0) ? "#92400E" : "#166534"))
                : (((backend ? backend.tier1Count : 0) > 0) ? "#FDA29B" : (((backend ? backend.tier2Count : 0) > 0) ? "#FEDF89" : "#75E0A7"))
            border.width: ((backend ? backend.tier1Count : 0) > 0) ? 2 : 1.5

            ColumnLayout {
                id: triageHubCol
                anchors.fill: parent
                anchors.margins: 20
                spacing: 16

                // ----------------------------------------------------
                // 1. MASTER HEADER & STATUS BAR (RTL)
                // ----------------------------------------------------
                RowLayout {
                    Layout.fillWidth: true
                    layoutDirection: Qt.RightToLeft
                    spacing: 14

                    // Status Icon in Circle
                    Rectangle {
                        width: 44; height: 44; radius: 22
                        color: Theme.dark
                            ? (((backend ? backend.tier1Count : 0) > 0) ? "#3B1215" : (((backend ? backend.tier2Count : 0) > 0) ? "#361E05" : "#062E1B"))
                            : (((backend ? backend.tier1Count : 0) > 0) ? "#FEF3F2" : (((backend ? backend.tier2Count : 0) > 0) ? "#FFFAEB" : "#ECFDF3"))
                        border.color: Theme.dark
                            ? (((backend ? backend.tier1Count : 0) > 0) ? "#7F1D1D" : (((backend ? backend.tier2Count : 0) > 0) ? "#78350F" : "#14532D"))
                            : (((backend ? backend.tier1Count : 0) > 0) ? "#FDA29B" : (((backend ? backend.tier2Count : 0) > 0) ? "#FEDF89" : "#75E0A7"))
                        Text {
                            anchors.centerIn: parent
                            text: ((backend ? backend.tier1Count : 0) > 0) ? "🚨" : (((backend ? backend.tier2Count : 0) > 0) ? "⚡" : "✓")
                            font.pixelSize: 22
                        }
                    }

                    // Status Title & Subtitle (Persian RTL)
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 3
                        Text {
                            Layout.fillWidth: true
                            horizontalAlignment: Text.AlignRight
                            text: ((backend ? backend.tier1Count : 0) > 0)
                                ? "اورژانس‌های حیاتی بالینی — نیازمند مداخله فوری (< ۲ ساعت)"
                                : (((backend ? backend.tier2Count : 0) > 0)
                                    ? "اقدامات تشخیصی تحت‌حاد و طبقه‌بندی خطر (۲۴ تا ۷۲ ساعت)"
                                    : "اطمینان‌بخشی فیزیولوژیک پایه — کلیه شاخص‌ها در محدوده بهینه")
                            color: Theme.dark
                                ? (((backend ? backend.tier1Count : 0) > 0) ? "#F87171" : (((backend ? backend.tier2Count : 0) > 0) ? "#FBBF24" : "#4ADE80"))
                                : (((backend ? backend.tier1Count : 0) > 0) ? "#B42318" : (((backend ? backend.tier2Count : 0) > 0) ? "#B54708" : "#067647"))
                            font.pixelSize: 14; font.bold: true
                        }
                        Text {
                            Layout.fillWidth: true
                            horizontalAlignment: Text.AlignRight
                            text: ((backend ? backend.tier1Count : 0) > 0)
                                ? "بررسی فوری بالینی توسط پزشک، نوار قلب و کنترل داروهای نفروتوکسیک در کمترین زمان الزامی است."
                                : (((backend ? backend.tier2Count : 0) > 0)
                                    ? "تست‌های تکمیلی استاندارد طلایی و پیگیری سرپایی جهت قطعیت تشخیصی و مداخله زودهنگام توصیه می‌شود."
                                    : "شواهدی از الگوی پاتولوژیک فعال مشاهده نشد؛ مراقبت‌های معمول و ارتقای سلامت کافی است.")
                            color: Theme.dark
                                ? (((backend ? backend.tier1Count : 0) > 0) ? "#FCA5A5" : (((backend ? backend.tier2Count : 0) > 0) ? "#FDE68A" : "#86EFAC"))
                                : (((backend ? backend.tier1Count : 0) > 0) ? "#912018" : (((backend ? backend.tier2Count : 0) > 0) ? "#7A2E0E" : "#054F31"))
                            font.pixelSize: 11
                            wrapMode: Text.Wrap
                        }
                    }

                    // Direct AI Button on Triage Header (Disabled for this release)
                    HgButton {
                        visible: false
                        text: "🤖 تحلیل AI →"
                        primary: true
                        implicitHeight: 32
                        font.pixelSize: 11
                        leftPadding: 12
                        rightPadding: 12
                        onClicked: backend.continueToChat()
                    }

                    // Triage Count Indicators (RTL Pills)
                    RowLayout {
                        spacing: 6
                        layoutDirection: Qt.RightToLeft

                        // Tier 1 Pill
                        Rectangle {
                            implicitWidth: t1PillText.implicitWidth + 16; height: 26; radius: 13
                            color: ((backend ? backend.tier1Count : 0) > 0) ? (Theme.dark ? "#7F1D1D" : "#B42318") : Theme.surfaceAlt
                            border.color: ((backend ? backend.tier1Count : 0) > 0) ? (Theme.dark ? "#991B1B" : "#B42318") : Theme.border
                            Text {
                                id: t1PillText; anchors.centerIn: parent
                                text: "فوری: " + (backend ? backend.tier1Count : 0)
                                color: ((backend ? backend.tier1Count : 0) > 0) ? "#FFFFFF" : Theme.muted
                                font.pixelSize: 10; font.bold: true
                            }
                        }

                        // Tier 2 Pill
                        Rectangle {
                            implicitWidth: t2PillText.implicitWidth + 16; height: 26; radius: 13
                            color: ((backend ? backend.tier2Count : 0) > 0) ? (Theme.dark ? "#78350F" : "#F79009") : Theme.surfaceAlt
                            border.color: ((backend ? backend.tier2Count : 0) > 0) ? (Theme.dark ? "#92400E" : "#F79009") : Theme.border
                            Text {
                                id: t2PillText; anchors.centerIn: parent
                                text: "تحت‌حاد: " + (backend ? backend.tier2Count : 0)
                                color: ((backend ? backend.tier2Count : 0) > 0) ? "#FFFFFF" : Theme.muted
                                font.pixelSize: 10; font.bold: true
                            }
                        }

                        // Tier 3 Pill
                        Rectangle {
                            implicitWidth: t3PillText.implicitWidth + 16; height: 26; radius: 13
                            color: ((backend ? backend.tier3Count : 0) > 0) ? (Theme.dark ? "#14532D" : "#12B76A") : Theme.surfaceAlt
                            border.color: ((backend ? backend.tier3Count : 0) > 0) ? (Theme.dark ? "#166534" : "#12B76A") : Theme.border
                            Text {
                                id: t3PillText; anchors.centerIn: parent
                                text: "اطمینان‌بخش: " + (backend ? backend.tier3Count : 0)
                                color: ((backend ? backend.tier3Count : 0) > 0) ? "#FFFFFF" : Theme.muted
                                font.pixelSize: 10; font.bold: true
                            }
                        }
                    }
                }

                Rectangle { Layout.fillWidth: true; height: 1; color: Theme.border; opacity: 0.7 }

                // ----------------------------------------------------
                // 2. 🔴 TIER 1 SECTION (Immediate Critical Findings < 2h)
                // ----------------------------------------------------
                Rectangle {
                    visible: (backend ? backend.tier1Count : 0) > 0
                    Layout.fillWidth: true
                    implicitHeight: t1InnerCol.implicitHeight + 24
                    radius: 12
                    color: Theme.dark ? "#261114" : "#FEF3F2"
                    border.color: Theme.dark ? "#5E1D24" : "#FDA29B"
                    border.width: 1.5

                    ColumnLayout {
                        id: t1InnerCol
                        anchors.fill: parent; anchors.margins: 14; spacing: 10

                        RowLayout {
                            Layout.fillWidth: true
                            layoutDirection: Qt.RightToLeft
                            spacing: 8
                            Text {
                                text: "🔴 سطح ۱: اورژانس‌های حیاتی بالینی (< ۲ ساعت)"
                                color: Theme.dark ? "#F87171" : "#B42318"
                                font.pixelSize: 13; font.bold: true
                                horizontalAlignment: Text.AlignRight
                            }
                            Item { Layout.fillWidth: true }
                            Rectangle {
                                implicitWidth: t1CountText.implicitWidth + 16; height: 22; radius: 11
                                color: Theme.dark ? "#7F1D1D" : "#B42318"
                                Text {
                                    id: t1CountText; anchors.centerIn: parent
                                    text: (backend ? backend.tier1Count : 0) + " مورد نیازمند اقدام فوری"
                                    color: "#FFFFFF"; font.pixelSize: 9; font.bold: true
                                }
                            }
                        }

                        Repeater {
                            model: backend ? backend.tier1CriticalRows : []
                            Rectangle {
                                required property var modelData
                                Layout.fillWidth: true
                                implicitHeight: t1ItemCol.implicitHeight + 20
                                radius: 10
                                color: Theme.dark ? "#180C0E" : "#FFFFFF"
                                border.color: Theme.dark ? "#47151B" : "#FECDCA"

                                ColumnLayout {
                                    id: t1ItemCol
                                    anchors.fill: parent; anchors.margins: 12; spacing: 8

                                    RowLayout {
                                        Layout.fillWidth: true
                                        layoutDirection: Qt.RightToLeft
                                        spacing: 8
                                        Text {
                                            Layout.fillWidth: true
                                            horizontalAlignment: Text.AlignRight
                                            text: "🚨 " + (modelData.title_fa || modelData.title)
                                            color: Theme.dark ? "#FCA5A5" : "#912018"
                                            font.pixelSize: 12; font.bold: true
                                            wrapMode: Text.Wrap
                                        }
                                        Rectangle {
                                            implicitWidth: t1TimeBadge.implicitWidth + 14; height: 20; radius: 10
                                            color: Theme.dark ? "#47151B" : "#FEE4E2"
                                            Text {
                                                id: t1TimeBadge; anchors.centerIn: parent
                                                text: modelData.timeframe || "< 2h"
                                                color: Theme.dark ? "#F87171" : "#B42318"
                                                font.pixelSize: 9; font.bold: true
                                            }
                                        }
                                    }

                                    Rectangle {
                                        Layout.fillWidth: true
                                        implicitHeight: t1ActRow.implicitHeight + 12
                                        radius: 6
                                        color: Theme.dark ? "#261114" : "#FEF3F2"
                                        border.color: Theme.dark ? "#47151B" : "#FECDCA"
                                        RowLayout {
                                            id: t1ActRow
                                            anchors.fill: parent; anchors.margins: 8
                                            layoutDirection: Qt.RightToLeft; spacing: 6
                                            Text { text: "⚡"; font.pixelSize: 12 }
                                            Text {
                                                Layout.fillWidth: true
                                                horizontalAlignment: Text.AlignRight
                                                text: "اقدام فوری: " + (modelData.action_fa || modelData.action_en)
                                                color: Theme.dark ? "#FCA5A5" : "#B42318"
                                                font.pixelSize: 11; font.weight: Font.DemiBold
                                                wrapMode: Text.Wrap
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

                // ----------------------------------------------------
                // 3. 🟡 TIER 2 SECTION (Dark Mode Protected: Zero Blinding White)
                // ----------------------------------------------------
                Rectangle {
                    visible: (backend ? backend.tier2Count : 0) > 0
                    Layout.fillWidth: true
                    implicitHeight: t2InnerCol.implicitHeight + 24
                    radius: 12
                    color: Theme.dark ? "#241808" : "#FFFAEB"
                    border.color: Theme.dark ? "#663806" : "#FEDF89"
                    border.width: 1.5

                    ColumnLayout {
                        id: t2InnerCol
                        anchors.fill: parent; anchors.margins: 14; spacing: 10

                        RowLayout {
                            Layout.fillWidth: true
                            layoutDirection: Qt.RightToLeft
                            spacing: 8
                            Text {
                                text: "🟡 سطح ۲: اقدامات تشخیصی تحت‌حاد و طبقه‌بندی خطر (۲۴ تا ۷۲ ساعت)"
                                color: Theme.dark ? "#FBBF24" : "#B54708"
                                font.pixelSize: 13; font.bold: true
                                horizontalAlignment: Text.AlignRight
                            }
                            Item { Layout.fillWidth: true }
                            Rectangle {
                                implicitWidth: t2CountText.implicitWidth + 16; height: 22; radius: 11
                                color: Theme.dark ? "#78350F" : "#F79009"
                                Text {
                                    id: t2CountText; anchors.centerIn: parent
                                    text: (backend ? backend.tier2Count : 0) + " یافته تشخیصی"
                                    color: "#FFFFFF"; font.pixelSize: 9; font.bold: true
                                }
                            }
                        }

                        Repeater {
                            model: (backend && backend.tier2ActionableRows) ? backend.tier2ActionableRows.slice(0, 5) : []
                            Rectangle {
                                required property var modelData
                                Layout.fillWidth: true
                                implicitHeight: t2ItemCol.implicitHeight + 20
                                radius: 10
                                color: Theme.dark ? "#160F04" : "#FFFFFF"
                                border.color: Theme.dark ? "#4A2803" : "#FEF0C7"

                                ColumnLayout {
                                    id: t2ItemCol
                                    anchors.fill: parent; anchors.margins: 12; spacing: 8

                                    RowLayout {
                                        Layout.fillWidth: true
                                        layoutDirection: Qt.RightToLeft
                                        spacing: 8
                                        Text {
                                            Layout.fillWidth: true
                                            horizontalAlignment: Text.AlignRight
                                            text: "🔸 " + (modelData.title_fa || modelData.title)
                                            color: Theme.dark ? "#FDE68A" : "#B54708"
                                            font.pixelSize: 12; font.bold: true
                                            wrapMode: Text.Wrap
                                        }
                                        Rectangle {
                                            implicitWidth: t2TimeBadge.implicitWidth + 14; height: 20; radius: 10
                                            color: Theme.dark ? "#3A2105" : "#FEF0C7"
                                            Text {
                                                id: t2TimeBadge; anchors.centerIn: parent
                                                text: modelData.timeframe || "24-72h"
                                                color: Theme.dark ? "#FBBF24" : "#B54708"
                                                font.pixelSize: 9; font.bold: true
                                            }
                                        }
                                    }

                                    Rectangle {
                                        Layout.fillWidth: true
                                        implicitHeight: t2ActRow.implicitHeight + 12
                                        radius: 6
                                        color: Theme.dark ? "#1F1505" : "#FFFAEB"
                                        border.color: Theme.dark ? "#3A2105" : "#FEF0C7"
                                        RowLayout {
                                            id: t2ActRow
                                            anchors.fill: parent; anchors.margins: 8
                                            layoutDirection: Qt.RightToLeft; spacing: 6
                                            Text { text: "↳"; font.pixelSize: 12; color: Theme.dark ? "#FBBF24" : "#B54708" }
                                            Text {
                                                Layout.fillWidth: true
                                                horizontalAlignment: Text.AlignRight
                                                text: "اقدام تکمیلی: " + (modelData.action_fa || modelData.action_en)
                                                color: Theme.dark ? "#C084FC" : "#5925DC"
                                                font.pixelSize: 11; font.weight: Font.DemiBold
                                                wrapMode: Text.Wrap
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

                // ----------------------------------------------------
                // 4. 🟢 TIER 3 SECTION (Physiological Reassurance & Baseline)
                // ----------------------------------------------------
                Rectangle {
                    visible: (backend ? backend.tier3Count : 0) > 0
                    Layout.fillWidth: true
                    implicitHeight: t3InnerCol.implicitHeight + 24
                    radius: 12
                    color: Theme.dark ? "#082115" : "#ECFDF3"
                    border.color: Theme.dark ? "#0D5E3A" : "#75E0A7"
                    border.width: 1.5

                    ColumnLayout {
                        id: t3InnerCol
                        anchors.fill: parent; anchors.margins: 14; spacing: 10

                        RowLayout {
                            Layout.fillWidth: true
                            layoutDirection: Qt.RightToLeft
                            spacing: 8
                            Text {
                                text: "🟢 سطح ۳: اطمینان‌بخشی فیزیولوژیک و پایش پایه (Physiological Reassurance)"
                                color: Theme.dark ? "#4ADE80" : "#067647"
                                font.pixelSize: 13; font.bold: true
                                horizontalAlignment: Text.AlignRight
                            }
                            Item { Layout.fillWidth: true }
                            Rectangle {
                                implicitWidth: t3CountText.implicitWidth + 16; height: 22; radius: 11
                                color: Theme.dark ? "#14532D" : "#12B76A"
                                Text {
                                    id: t3CountText; anchors.centerIn: parent
                                    text: (backend ? backend.tier3Count : 0) + " شاخص نرمال و اطمینان‌بخش"
                                    color: "#FFFFFF"; font.pixelSize: 9; font.bold: true
                                }
                            }
                        }

                        Repeater {
                            model: backend ? backend.tier3PhysiologicalRows : []
                            Rectangle {
                                required property var modelData
                                Layout.fillWidth: true
                                implicitHeight: t3ItemCol.implicitHeight + 18
                                radius: 10
                                color: Theme.dark ? "#04140D" : "#FFFFFF"
                                border.color: Theme.dark ? "#0A4329" : "#D1FADF"

                                ColumnLayout {
                                    id: t3ItemCol
                                    anchors.fill: parent; anchors.margins: 12; spacing: 6

                                    RowLayout {
                                        Layout.fillWidth: true
                                        layoutDirection: Qt.RightToLeft
                                        spacing: 8
                                        Text {
                                            Layout.fillWidth: true
                                            horizontalAlignment: Text.AlignRight
                                            text: "✓ " + (modelData.title_fa || modelData.title)
                                            color: Theme.dark ? "#86EFAC" : "#067647"
                                            font.pixelSize: 12; font.bold: true
                                            wrapMode: Text.Wrap
                                        }
                                    }

                                    Text {
                                        Layout.fillWidth: true
                                        horizontalAlignment: Text.AlignRight
                                        text: modelData.details_fa || modelData.details_en
                                        color: Theme.dark ? "#CBD5E1" : "#344054"
                                        font.pixelSize: 11
                                        wrapMode: Text.Wrap
                                    }
                                }
                            }
                        }
                    }
                }

                // ----------------------------------------------------
                // 5. 📋 COLLAPSIBLE CLINICAL EXECUTIVE SUMMARY (RTL)
                // ----------------------------------------------------
                Rectangle {
                    visible: Boolean(backend && backend.executiveSummary && backend.executiveSummary.length > 0)
                    Layout.fillWidth: true
                    implicitHeight: execCardCol.implicitHeight + 20
                    radius: 12
                    color: Theme.surfaceAlt
                    border.color: Theme.border

                    ColumnLayout {
                        id: execCardCol
                        anchors.fill: parent; anchors.margins: 14; spacing: 10

                        RowLayout {
                            Layout.fillWidth: true
                            layoutDirection: Qt.RightToLeft
                            spacing: 10

                            Text {
                                text: "📋 خلاصه جامع بالینی پرونده (Clinical Executive Summary)"
                                color: Theme.text; font.pixelSize: 13; font.bold: true
                                horizontalAlignment: Text.AlignRight
                            }

                            Rectangle {
                                visible: Boolean(backend && backend.targetPopulationInfo && backend.targetPopulationInfo.length > 0)
                                implicitWidth: popBadgeText.implicitWidth + 14; height: 22; radius: 11
                                color: Theme.dark ? "#102A4C" : "#EFF8FF"
                                border.color: Theme.dark ? "#1D4ED8" : "#B2DDFF"
                                Text {
                                    id: popBadgeText; anchors.centerIn: parent
                                    text: (backend ? backend.targetPopulationInfo : "") || ""
                                    color: Theme.dark ? "#93C5FD" : "#175CD3"
                                    font.pixelSize: 10; font.bold: true
                                }
                            }

                            Item { Layout.fillWidth: true }

                            // 🌟 DIRECT AI SUMMARY PRESENTATION BUTTON (Disabled for this release)
                            HgButton {
                                visible: false
                                text: "💬 تحلیل و ارائه‌ی کامل خلاصه با AI →"
                                primary: true
                                implicitHeight: 30
                                font.pixelSize: 11
                                leftPadding: 14
                                rightPadding: 14
                                onClicked: backend.continueToChat()
                            }

                            Rectangle {
                                implicitWidth: toggleSumText.implicitWidth + 20; height: 28; radius: 14
                                color: toggleSumMouse.containsMouse ? Theme.surface : "transparent"
                                border.color: Theme.border
                                Text {
                                    id: toggleSumText
                                    anchors.centerIn: parent
                                    text: root.summaryExpanded ? "بستن خلاصه ▲" : "مشاهده متن کامل خلاصه ▼"
                                    color: Theme.accent; font.pixelSize: 11; font.bold: true
                                }
                                MouseArea {
                                    id: toggleSumMouse
                                    anchors.fill: parent
                                    hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                                    onClicked: root.summaryExpanded = !root.summaryExpanded
                                }
                            }
                        }

                        Rectangle {
                            visible: root.summaryExpanded
                            Layout.fillWidth: true
                            implicitHeight: execSummaryText.implicitHeight + 20
                            radius: 10
                            color: Theme.surface
                            border.color: Theme.border

                            TextEdit {
                                id: execSummaryText
                                anchors.fill: parent
                                anchors.margins: 14
                                readOnly: true
                                selectByMouse: true
                                wrapMode: TextEdit.Wrap
                                horizontalAlignment: Text.AlignRight
                                text: (backend ? backend.executiveSummary : "") || ""
                                color: Theme.text
                                font.pixelSize: 12
                                font.family: Theme.fontFamily
                                textFormat: TextEdit.PlainText

                                // Forward mouse wheel over text area so page still scrolls smoothly
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
                            }
                        }

                        // 🌟 BIG FOOTER BUTTON TO JUMP DIRECTLY INTO AI
                        RowLayout {
                            visible: false
                            Layout.fillWidth: true
                            layoutDirection: Qt.RightToLeft
                            spacing: 10

                            HgButton {
                                text: "💬 شروع تحلیل جامع و پرسش‌وپاسخ با دستیار هوش مصنوعی (AI Chat) →"
                                primary: true
                                implicitHeight: 38
                                leftPadding: 20
                                rightPadding: 20
                                font.pixelSize: 12
                                font.bold: true
                                onClicked: backend.continueToChat()
                            }
                        }
                    }
                }
            }
        }

        // ============================================================
        // ✅ PATIENT CONTEXT (Non-blood information, scrollable)
        // ============================================================
        HgCard {
            visible: Boolean(backend && backend.patientContextRows && backend.patientContextRows.length > 0)
            Layout.fillWidth: true
            implicitHeight: ctxCardCol.implicitHeight + 30
            ColumnLayout {
                id: ctxCardCol
                anchors.fill: parent; anchors.margins: 18; spacing: 10
                RowLayout {
                    Layout.fillWidth: true; spacing: 8
                    Text { text: "PATIENT CONTEXT"; color: Theme.muted; font.pixelSize: 11; font.bold: true; font.letterSpacing: 1.5 }
                    Item { Layout.fillWidth: true }
                    Rectangle {
                        implicitWidth: ctxCountText.implicitWidth + 16; height: 22; radius: 11
                        color: Theme.dark ? "#102A4C" : "#EFF8FF"
                        Text { id: ctxCountText; anchors.centerIn: parent; text: (backend && backend.patientContextRows ? backend.patientContextRows.length : 0) + " items"; color: Theme.dark ? "#93C5FD" : "#175CD3"; font.pixelSize: 9; font.bold: true }
                    }
                }
                Rectangle { Layout.fillWidth: true; height: 1; color: Theme.border }
                Flickable {
                    Layout.fillWidth: true
                    implicitHeight: Math.min(ctxFlow.implicitHeight, 180)
                    contentWidth: width
                    contentHeight: ctxFlow.implicitHeight
                    clip: true
                    boundsBehavior: Flickable.StopAtBounds
                    ScrollBar.vertical: ScrollBar {}
                    Flow {
                        id: ctxFlow
                        width: parent.width
                        spacing: 8
                        Repeater {
                            model: backend ? backend.patientContextRows : []
                            Rectangle {
                                required property var modelData
                                implicitWidth: ctxItemCol.implicitWidth + 24
                                implicitHeight: ctxItemCol.implicitHeight + 16
                                radius: 10
                                color: Theme.surfaceAlt
                                border.color: Theme.border
                                ColumnLayout {
                                    id: ctxItemCol
                                    anchors.centerIn: parent; spacing: 2
                                    Text { text: modelData.label; color: Theme.muted; font.pixelSize: 9; font.weight: Font.DemiBold }
                                    Text { text: modelData.value; color: Theme.text; font.pixelSize: 12; font.bold: true }
                                }
                            }
                        }
                    }
                }
            }
        }

        // ============================================================
        // STAT CARDS
        // ============================================================
        RowLayout {
            Layout.fillWidth: true; spacing: 14
            StatCard { Layout.fillWidth: true; number: backend ? backend.measuredCount : 0; label: "Measured" }
            StatCard { Layout.fillWidth: true; number: backend ? backend.derivedCount : 0; label: "Calculated" }
            StatCard { Layout.fillWidth: true; number: backend ? backend.tier1Count : 0; label: "Tier 1: Urgent (< 2h)"; accentColor: (backend && backend.tier1Count) ? "#B42318" : Theme.text }
            StatCard { Layout.fillWidth: true; number: backend ? backend.tier2Count : 0; label: "Tier 2: Actionable"; accentColor: (backend && backend.tier2Count) ? "#B54708" : Theme.text }
            StatCard { Layout.fillWidth: true; number: backend ? backend.tier3Count : 0; label: "Tier 3: Reassurance"; accentColor: (backend && backend.tier3Count) ? "#067647" : Theme.text }
            StatCard { Layout.fillWidth: true; number: (backend && backend.filteredRiskRows ? backend.filteredRiskRows.length : 0); label: "Risk Models" }
        }

        // ============================================================
        // GLOBAL SEARCH
        // ============================================================
        TextField {
            Layout.fillWidth: true
            implicitHeight: 46
            placeholderText: "Search across all results, features, and models..."
            color: Theme.text
            placeholderTextColor: Theme.muted
            horizontalAlignment: TextInput.AlignLeft
            verticalAlignment: TextInput.AlignVCenter
            leftPadding: 16
            rightPadding: 16
            font.family: Theme.fontFamily
            font.pixelSize: 13
            onTextChanged: root.filterText = text.toLowerCase()
            background: Rectangle { radius: 14; color: Theme.surface; border.color: activeFocus ? Theme.accent : Theme.border }
        }

        // ============================================================
        // MEASURED & DERIVED
        // ============================================================
        RowLayout {
            Layout.fillWidth: true; implicitHeight: 450; spacing: 18
            ResultPanel { Layout.fillWidth: true; title: "MEASURED FEATURES"; sourceRows: backend ? backend.measuredRows : []; derivedMode: false; filterText: root.filterText }
            ResultPanel { Layout.fillWidth: true; title: "DERIVED FEATURES"; sourceRows: backend ? backend.derivedRows : []; derivedMode: true; filterText: root.filterText }
        }

        // ============================================================
        // CLINICAL INTERPRETATIONS
        // ============================================================
        ColumnLayout {
            Layout.fillWidth: true; spacing: 12
            Text { text: "Clinical Interpretations"; color: Theme.text; font.pixelSize: 22; font.weight: Font.Bold; Layout.topMargin: 12 }
            Text { text: "Disease criteria and compatible laboratory patterns based on JSON guideline rules."; color: Theme.muted; font.pixelSize: 12 }
            TextField {
                Layout.fillWidth: true; implicitHeight: 42
                placeholderText: "Filter interpretations by disease name or ID..."
                color: Theme.text
                placeholderTextColor: Theme.muted
                horizontalAlignment: TextInput.AlignLeft
                verticalAlignment: TextInput.AlignVCenter
                leftPadding: 14
                rightPadding: 14
                font.family: Theme.fontFamily
                font.pixelSize: 13
                onTextChanged: root.clinicalFilterText = text.toLowerCase()
                background: Rectangle { radius: 12; color: Theme.surface; border.color: activeFocus ? Theme.accent : Theme.border }
            }
            RowLayout {
                Layout.fillWidth: true; implicitHeight: 560; spacing: 18
                InterpretationPanel {
                    Layout.fillWidth: true; title: "🩺 DISEASE CRITERIA"; hint: "Diagnostic / classification criteria met"
                    kindFilter: "disease"
                    badgeColor: Theme.dark ? "#3A2105" : "#FFF1D6"
                    badgeTextColor: Theme.dark ? "#FDE68A" : "#B54708"
                    filterText: root.filterText; clinicalFilter: root.clinicalFilterText
                }
                InterpretationPanel {
                    Layout.fillWidth: true; title: "🧬 COMPATIBLE PATTERNS"; hint: "Compatible · possible · screening · urgent"
                    kindFilter: "pattern"
                    badgeColor: Theme.dark ? "#102A4C" : "#EFF8FF"
                    badgeTextColor: Theme.dark ? "#93C5FD" : "#175CD3"
                    filterText: root.filterText; clinicalFilter: root.clinicalFilterText
                }
            }
        }

        // ============================================================
        // ✅ SCIENTIFIC RISK PREDICTIONS (filtered: Evaluated only)
        // ============================================================
        ColumnLayout {
            Layout.fillWidth: true; spacing: 12
            RowLayout {
                Layout.fillWidth: true
                ColumnLayout {
                    spacing: 2
                    Text { text: "Validated Scientific Risk Models"; color: Theme.text; font.pixelSize: 22; font.weight: Font.Bold; Layout.topMargin: 16 }
                    Text {
                        text: "Fully-evaluated peer-reviewed equations. Models with missing data or already-diagnosed conditions are shown in Guidelines."
                        color: Theme.muted; font.pixelSize: 12; wrapMode: Text.Wrap; Layout.maximumWidth: 800
                    }
                }
                Item { Layout.fillWidth: true }
                Rectangle {
                    implicitWidth: riskCountText.implicitWidth + 24; height: 30; radius: 15
                    color: Theme.dark ? "#102A4C" : "#EFF8FF"
                    border.color: Theme.dark ? "#1D4ED8" : "#B2DDFF"
                    Text { id: riskCountText; anchors.centerIn: parent; text: (backend && backend.filteredRiskRows ? backend.filteredRiskRows.length : 0) + " models evaluated"; color: Theme.dark ? "#93C5FD" : "#175CD3"; font.pixelSize: 10; font.bold: true }
                }
            }
            TextField {
                Layout.fillWidth: true; implicitHeight: 42
                placeholderText: "Filter risk models by name, citation, or disease..."
                color: Theme.text
                placeholderTextColor: Theme.muted
                horizontalAlignment: TextInput.AlignLeft
                verticalAlignment: TextInput.AlignVCenter
                leftPadding: 14
                rightPadding: 14
                font.family: Theme.fontFamily
                font.pixelSize: 13
                onTextChanged: root.riskFilterText = text.toLowerCase()
                background: Rectangle { radius: 12; color: Theme.surface; border.color: activeFocus ? Theme.accent : Theme.border }
            }
            ColumnLayout {
                Layout.fillWidth: true; spacing: 14
                Repeater {
                    model: backend ? backend.filteredRiskRows : []
                    delegate: RiskCard {
                        Layout.fillWidth: true
                        riskFilter: root.riskFilterText
                        globalFilter: root.filterText
                    }
                }
            }
            Rectangle {
                visible: !(backend && backend.filteredRiskRows && backend.filteredRiskRows.length > 0)
                Layout.fillWidth: true; implicitHeight: 80; radius: 16
                color: Theme.surfaceAlt; border.color: Theme.border
                Text {
                    anchors.centerIn: parent
                    text: (backend && backend.riskRows && backend.riskRows.length > 0)
                        ? "No fully-evaluated risk models. Add measurements (e.g., Lipids, eGFR, HbA1c) to enable more models."
                        : "No risk predictions available. Add more measurements to see scientific forecasts."
                    color: Theme.muted; font.pixelSize: 12; wrapMode: Text.Wrap; horizontalAlignment: Text.AlignHCenter
                }
            }
        }

        // ============================================================
        // ACTION BAR
        // ============================================================
        RowLayout {
            Layout.fillWidth: true; Layout.topMargin: 12; Layout.bottomMargin: 24; spacing: 12
            HgButton { text: "+ New analysis"; onClicked: backend ? backend.newAnalysis() : null }
            Item { Layout.fillWidth: true }
            Rectangle {
                visible: Boolean(backend && backend.analysisSaved)
                implicitWidth: savedLabel.implicitWidth + 24; height: 38; radius: 12
                color: Theme.dark ? "#082F1D" : "#ECFDF3"
                border.color: Theme.dark ? "#085D3A" : "#75E0A7"
                Text { id: savedLabel; anchors.centerIn: parent; text: "Saved to history ✓"; color: Theme.dark ? "#86EFAC" : "#067647"; font.pixelSize: 11; font.bold: true }
            }
            HgButton { text: "Save analysis"; enabled: Boolean(backend && !backend.analysisSaved); onClicked: backend ? backend.saveAnalysis() : null }
            HgButton { text: "Edit measurements →"; enabled: Boolean(backend && backend.hasCurrentAnalysis); onClicked: backend ? backend.editAnalysis() : null }
            HgButton { visible: false; text: "💬 ارائه‌ی خلاصه و چت با هوش مصنوعی →"; primary: true; onClicked: backend ? backend.continueToChat() : null }
        }
    }

    // ================================================================
    // COMPONENTS
    // ================================================================
    component StatCard: HgCard {
        required property int number
        required property string label
        property color accentColor: Theme.text
        implicitHeight: 84
        Column {
            anchors.centerIn: parent; spacing: 4
            Text { anchors.horizontalCenter: parent.horizontalCenter; text: number; color: accentColor; font.pixelSize: 26; font.bold: true }
            Text { anchors.horizontalCenter: parent.horizontalCenter; text: label; color: Theme.muted; font.pixelSize: 10; font.weight: Font.DemiBold }
        }
    }

    // ✅ ResultPanel — supports BOTH measured (with flag) and derived (no flag)
    component ResultPanel: HgCard {
        id: panel
        required property string title
        required property var sourceRows
        required property bool derivedMode
        required property string filterText
        implicitHeight: 450
        ColumnLayout {
            anchors.fill: parent; anchors.margins: 18; spacing: 10
            Text { text: panel.title; color: Theme.muted; font.pixelSize: 11; font.bold: true; font.letterSpacing: 1.5 }
            Rectangle { Layout.fillWidth: true; height: 1; color: Theme.border }
            ListView {
                Layout.fillWidth: true; Layout.fillHeight: true
                model: panel.sourceRows
                clip: true; spacing: 4
                ScrollBar.vertical: ScrollBar {}
                delegate: Item {
                    required property string featureId
                    required property string featureName
                    required property string value
                    required property string unit
                    required property string category
                    required property string formula
                    required property string flag
                    width: ListView.view.width
                    visible: !panel.filterText.length || (featureName + " " + featureId + " " + category + " " + formula).toLowerCase().indexOf(panel.filterText) >= 0
                    height: visible ? 58 : 0
                    Rectangle { anchors.left: parent.left; anchors.right: parent.right; anchors.bottom: parent.bottom; height: 1; color: Theme.border; opacity: 0.5 }
                    RowLayout {
                        anchors.fill: parent; spacing: 10
                        ColumnLayout {
                            Layout.fillWidth: true; spacing: 2
                            Text { text: featureName.length > 0 ? featureName : featureId; color: Theme.text; font.pixelSize: 13; font.weight: Font.DemiBold; elide: Text.ElideRight; Layout.fillWidth: true }
                            Text {
                                text: panel.derivedMode && formula.length > 0 ? formula : (category.length > 0 ? category : featureId)
                                color: Theme.muted; font.pixelSize: 10; font.family: panel.derivedMode ? "Courier New" : Theme.fontFamily; elide: Text.ElideRight; Layout.fillWidth: true
                            }
                        }
                        Text { text: value; color: Theme.text; font.pixelSize: 14; font.bold: true }
                        Text { visible: unit.length > 0; text: unit; color: Theme.muted; font.pixelSize: 11; Layout.preferredWidth: 60; elide: Text.ElideRight }

                        // Flag Badge: Only for measured features
                        Rectangle {
                            visible: !panel.derivedMode && flag.length > 0
                            implicitWidth: flagText.implicitWidth + 14
                            height: 22
                            radius: 11
                            color: {
                                var f = (flag || "").toUpperCase()
                                if (f === "H" || f === "HIGH" || f === "HH" || f === "CRIT" || f === "CRITICAL") return Theme.dark ? "#47151B" : "#FEE4E2"
                                if (f === "L" || f === "LOW" || f === "LL") return Theme.dark ? "#3A2105" : "#FEF0C7"
                                if (f === "B" || f === "BORDERLINE") return Theme.dark ? "#3A2105" : "#FEF0C7"
                                return Theme.dark ? "#172033" : "#F2F4F7"
                            }
                            border.color: {
                                var f = (flag || "").toUpperCase()
                                if (f === "H" || f === "HIGH" || f === "HH" || f === "CRIT" || f === "CRITICAL") return Theme.dark ? "#7A271A" : "#FDA29B"
                                if (f === "L" || f === "LOW" || f === "LL") return Theme.dark ? "#78350F" : "#FEC84B"
                                if (f === "B" || f === "BORDERLINE") return Theme.dark ? "#78350F" : "#FEC84B"
                                return Theme.border
                            }
                            Text {
                                id: flagText; anchors.centerIn: parent
                                text: flag
                                color: {
                                    var f = (flag || "").toUpperCase()
                                    if (f === "H" || f === "HIGH" || f === "HH" || f === "CRIT" || f === "CRITICAL") return Theme.dark ? "#FCA5A5" : "#B42318"
                                    if (f === "L" || f === "LOW" || f === "LL") return Theme.dark ? "#FDE68A" : "#B54708"
                                    if (f === "B" || f === "BORDERLINE") return Theme.dark ? "#FDE68A" : "#B54708"
                                    return Theme.dark ? "#94A3B8" : "#667085"
                                }
                                font.pixelSize: 9; font.bold: true
                            }
                        }
                    }
                }
            }
        }
    }

    component InterpretationPanel: HgCard {
        id: panel
        required property string title
        required property string hint
        required property string kindFilter
        required property color badgeColor
        required property color badgeTextColor
        required property string filterText
        required property string clinicalFilter
        implicitHeight: 560
        ColumnLayout {
            anchors.fill: parent; anchors.margins: 18; spacing: 10
            RowLayout {
                Layout.fillWidth: true; spacing: 10
                ColumnLayout {
                    spacing: 2
                    Text { text: panel.title; color: Theme.text; font.pixelSize: 14; font.weight: Font.Bold }
                    Text { text: panel.hint; color: Theme.muted; font.pixelSize: 10 }
                }
                Item { Layout.fillWidth: true }
                Rectangle {
                    implicitWidth: cntText.implicitWidth + 20; height: 26; radius: 13
                    color: panel.badgeColor
                    Text { id: cntText; anchors.centerIn: parent; text: root.countKind(panel.kindFilter); color: panel.badgeTextColor; font.pixelSize: 11; font.bold: true }
                }
            }
            Rectangle { Layout.fillWidth: true; height: 1; color: Theme.border }
            ListView {
                Layout.fillWidth: true; Layout.fillHeight: true
                model: backend ? backend.clinicalRows : []
                clip: true; spacing: 12
                ScrollBar.vertical: ScrollBar {}
                delegate: HgCard {
                    required property string diseaseId
                    required property string name
                    required property string status
                    required property string statusLabel
                    required property string urgency
                    required property string evidence
                    required property string limitations
                    required property string sources
                    required property string ruleId
                    required property string statement
                    required property string kind
                    width: ListView.view.width
                    implicitHeight: detailColumn.implicitHeight + 32
                    visible: kind === panel.kindFilter &&
                        (!panel.filterText.length || (name + " " + diseaseId).toLowerCase().indexOf(panel.filterText) >= 0) &&
                        (!panel.clinicalFilter.length || (name + " " + diseaseId + " " + evidence).toLowerCase().indexOf(panel.clinicalFilter) >= 0)
                    height: visible ? implicitHeight : 0
                    ColumnLayout {
                        id: detailColumn
                        anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top
                        anchors.margins: 16; spacing: 8
                        RowLayout {
                            Layout.fillWidth: true
                            Text { text: name; color: Theme.text; font.pixelSize: 15; font.weight: Font.DemiBold; Layout.fillWidth: true }
                            Rectangle {
                                implicitWidth: statusText.implicitWidth + 22; height: 28; radius: 14
                                color: {
                                    if (Theme.dark) {
                                        if (status === "urgent_pattern") return "#47151B"
                                        if (status === "criterion_met") return "#3A2105"
                                        if (status === "screening_positive") return "#102A4C"
                                        return "#361E05"
                                    }
                                    if (status === "urgent_pattern") return "#FEE4E2"
                                    if (status === "criterion_met") return "#FFF1D6"
                                    if (status === "screening_positive") return "#EFF8FF"
                                    return "#FEF0C7"
                                }
                                Text {
                                    id: statusText; anchors.centerIn: parent
                                    text: statusLabel
                                    color: {
                                        if (Theme.dark) {
                                            if (status === "urgent_pattern") return "#FCA5A5"
                                            if (status === "criterion_met") return "#FDE68A"
                                            if (status === "screening_positive") return "#93C5FD"
                                            return "#FBBF24"
                                        }
                                        if (status === "urgent_pattern") return "#B42318"
                                        if (status === "criterion_met") return "#B54708"
                                        if (status === "screening_positive") return "#175CD3"
                                        return "#B54708"
                                    }
                                    font.pixelSize: 10; font.bold: true
                                }
                            }
                        }
                        Text { text: statement; visible: statement.length > 0; color: Theme.text; opacity: .9; font.pixelSize: 12; wrapMode: Text.Wrap; Layout.fillWidth: true }
                        Text { text: "Evidence: " + evidence; visible: evidence.length > 0; color: Theme.muted; font.pixelSize: 11; wrapMode: Text.Wrap; Layout.fillWidth: true }
                        Text { text: "Limitations: " + limitations; visible: limitations.length > 0; color: Theme.warning; font.pixelSize: 10; wrapMode: Text.Wrap; Layout.fillWidth: true }
                        Text { text: "Sources: " + sources; visible: sources.length > 0; color: Theme.violet; font.pixelSize: 10; wrapMode: Text.Wrap; Layout.fillWidth: true }
                    }
                }
            }
            Text {
                visible: root.countKind(panel.kindFilter) === 0
                Layout.fillWidth: true; Layout.bottomMargin: 10; horizontalAlignment: Text.AlignHCenter; wrapMode: Text.Wrap
                text: panel.kindFilter === "disease" ? "No disease criterion is met." : "No compatible laboratory pattern."
                color: Theme.muted; font.pixelSize: 12
            }
        }
    }

    // ================================================================
    // ✅ RiskCard — Dark Mode Protected
    // ================================================================
    component RiskCard: HgCard {
        id: riskCard
        required property string diseaseKey
        required property string nameEn
        required property real probability
        required property real horizonYears
        required property string riskLevel
        required property string status
        required property string missingFeatures
        required property string exclusionReason
        required property string modelName
        required property string citation
        required property string doi
        required property string journal
        required property string publicationYear
        required property string referenceUrl
        required property string interpretationFa
        required property string riskBand
        required property string kind
        required property string scoreText
        required property string warnings
        required property string requiredFeatures

        property string riskFilter: ""
        property string globalFilter: ""
        property string searchHaystack: (nameEn + " " + diseaseKey + " " + modelName + " " +
            citation + " " + journal + " " + interpretationFa).toLowerCase()

        visible: (riskFilter.length === 0 || searchHaystack.indexOf(riskFilter) >= 0) &&
            (globalFilter.length === 0 || searchHaystack.indexOf(globalFilter) >= 0)
        height: visible ? implicitHeight : 0
        implicitHeight: visible ? cardCol.implicitHeight + 32 : 0

        ColumnLayout {
            id: cardCol
            anchors.fill: parent
            anchors.margins: 16
            spacing: 12

            RowLayout {
                Layout.fillWidth: true; spacing: 12
                ColumnLayout {
                    Layout.fillWidth: true; spacing: 3
                    RowLayout {
                        Layout.fillWidth: true; spacing: 8
                        Text {
                            text: modelName.length > 0 ? modelName : nameEn
                            color: Theme.text; font.pixelSize: 16; font.weight: Font.Bold
                            elide: Text.ElideRight; Layout.fillWidth: true
                        }
                        Rectangle {
                            visible: kind.length > 0
                            implicitWidth: kindText.implicitWidth + 16; height: 22; radius: 11
                            color: Theme.dark ? "#172033" : "#F2F4F7"
                            Text { id: kindText; anchors.centerIn: parent; text: kind.replace(/_/g, " "); color: Theme.dark ? "#94A3B8" : "#667085"; font.pixelSize: 9; font.bold: true }
                        }
                    }
                    RowLayout {
                        spacing: 8
                        Text {
                            visible: horizonYears > 0
                            text: horizonYears + "-Year Horizon"
                            color: Theme.accent; font.pixelSize: 11; font.bold: true
                        }
                        Text { visible: horizonYears > 0; text: "•"; color: Theme.muted; font.pixelSize: 11 }
                        Text { text: diseaseKey.replace(/_/g, " "); color: Theme.muted; font.pixelSize: 11; elide: Text.ElideRight; Layout.fillWidth: true }
                    }
                }
                Item { Layout.fillWidth: true }
                Rectangle {
                    implicitWidth: statusText.implicitWidth + 24; height: 30; radius: 15
                    color: {
                        if (Theme.dark) {
                            if (riskLevel === "Very High") return "#47151B"
                            if (riskLevel === "High") return "#3A2105"
                            if (riskLevel === "Moderate") return "#361E05"
                            if (riskLevel === "Low") return "#082F1D"
                            return "#172033"
                        }
                        if (riskLevel === "Very High") return "#FEE4E2"
                        if (riskLevel === "High") return "#FFF1D6"
                        if (riskLevel === "Moderate") return "#FEF0C7"
                        if (riskLevel === "Low") return "#ECFDF3"
                        return "#F2F4F7"
                    }
                    Text {
                        id: statusText; anchors.centerIn: parent
                        text: riskBand.length > 0 ? riskBand : riskLevel
                        color: {
                            if (Theme.dark) {
                                if (riskLevel === "Very High") return "#FCA5A5"
                                if (riskLevel === "High") return "#FDE68A"
                                if (riskLevel === "Moderate") return "#FBBF24"
                                if (riskLevel === "Low") return "#86EFAC"
                                return "#94A3B8"
                            }
                            if (riskLevel === "Very High") return "#B42318"
                            if (riskLevel === "High") return "#B54708"
                            if (riskLevel === "Moderate") return "#B54708"
                            if (riskLevel === "Low") return "#067647"
                            return "#667085"
                        }
                        font.pixelSize: 10; font.bold: true
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true; spacing: 14
                ColumnLayout {
                    spacing: 2
                    Text { text: "Probability"; color: Theme.muted; font.pixelSize: 9; font.weight: Font.DemiBold; font.letterSpacing: 1 }
                    Text {
                        text: Math.round(probability * 100) + "%"
                        color: (riskLevel === "Very High" || riskLevel === "High") ? Theme.danger : Theme.accent
                        font.pixelSize: 28; font.bold: true
                    }
                }
                Rectangle { Layout.preferredWidth: 1; Layout.fillHeight: true; color: Theme.border }
                ColumnLayout {
                    Layout.fillWidth: true; spacing: 4
                    Text { visible: scoreText.length > 0; text: "Score: " + scoreText; color: Theme.text; font.pixelSize: 12; font.bold: true }
                    Text {
                        visible: interpretationFa.length > 0
                        text: interpretationFa; color: Theme.text; opacity: 0.85; font.pixelSize: 12
                        wrapMode: Text.Wrap; Layout.fillWidth: true
                    }
                }
            }

            Rectangle {
                visible: warnings.length > 0
                Layout.fillWidth: true; implicitHeight: warnText.implicitHeight + 20; radius: 10
                color: Theme.dark ? "#381014" : "#FEF3F2"
                border.color: Theme.dark ? "#7A271A" : "#FDA29B"
                Text { id: warnText; anchors.fill: parent; anchors.margins: 10; text: "⚠ " + warnings; color: Theme.dark ? "#FCA5A5" : "#B42318"; font.pixelSize: 10; wrapMode: Text.Wrap }
            }

            Rectangle {
                visible: citation.length > 0 || doi.length > 0
                Layout.fillWidth: true; height: 1; color: Theme.border; opacity: 0.5
            }

            ColumnLayout {
                visible: citation.length > 0 || doi.length > 0
                Layout.fillWidth: true; spacing: 4
                Text {
                    visible: citation.length > 0
                    text: "📖 " + citation
                    color: Theme.muted; font.pixelSize: 10; font.italic: true
                    wrapMode: Text.Wrap; Layout.fillWidth: true
                }
                RowLayout {
                    Layout.fillWidth: true; spacing: 8
                    Text {
                        text: {
                            var c = citation.length > 0 ? citation : "Scientific Publication"
                            if (publicationYear.length > 0) c += " (" + publicationYear + ")"
                            return c
                        }
                        color: Theme.muted; font.pixelSize: 10; elide: Text.ElideRight; Layout.fillWidth: true
                    }
                    Rectangle {
                        visible: referenceUrl.length > 0 || doi.length > 0
                        implicitWidth: openText.implicitWidth + 20; height: 26; radius: 13
                        color: openArea.containsMouse ? Theme.accent : "transparent"
                        border.color: Theme.accent; border.width: 1
                        Text { id: openText; anchors.centerIn: parent; text: "Open Paper ↗"; color: openArea.containsMouse ? "#FFFFFF" : Theme.accent; font.pixelSize: 10; font.bold: true }
                        MouseArea {
                            id: openArea; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                            onClicked: {
                                var url = ""
                                if (referenceUrl.length > 0 && referenceUrl.indexOf("http") === 0) url = referenceUrl
                                else if (doi.length > 0) url = "https://doi.org/" + doi
                                if (url.length > 0) Qt.openUrlExternally(url)
                            }
                        }
                    }
                }
            }
        }
    }
}
