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
        id: riskVbar
        policy: root.contentHeight > root.height ? ScrollBar.AlwaysOn : ScrollBar.AsNeeded
        width: 10
        anchors.right: parent.right
        anchors.rightMargin: 3
        contentItem: Rectangle {
            implicitWidth: 10; radius: 5
            color: Theme.dark
                ? (riskVbar.pressed ? "#94A3B8" : (riskVbar.hovered ? "#64748B" : "#475569"))
                : (riskVbar.pressed ? "#475467" : (riskVbar.hovered ? "#98A2B3" : "#CBD5E1"))
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

    // ------------------------------------------------------------------
    // State
    // ------------------------------------------------------------------
    property string filterText: ""
    property string kindFilter: "All"

    property var catalog: (backend && backend.riskModelCatalog !== undefined && backend.riskModelCatalog !== null)
                          ? backend.riskModelCatalog : []

    // ------------------------------------------------------------------
    // Stats (single pass)
    // ------------------------------------------------------------------
    property var stats: {
        var src = root.catalog
        var st = { total: src.length, eq: 0, score: 0, crit: 0, heur: 0, cohort: 0 }
        for (var i = 0; i < src.length; i++) {
            var m = src[i] || {}
            var k = String(m.kind || "")
            if (String(m.modelName || "").indexOf("Multi-Cohort") >= 0) st.cohort++
            if (k === "validated_equation") st.eq++
            else if (k === "validated_score" || k === "validated_screen") st.score++
            else if (k === "validated_criteria" || k === "staging_system" || k === "biomarker_index") st.crit++
            else if (k === "heuristic") st.heur++
        }
        return st
    }

    // ------------------------------------------------------------------
    // Filtered catalog (JS — always works)
    // ------------------------------------------------------------------
    property var filteredCatalog: {
        var src = root.catalog
        var out = []
        for (var i = 0; i < src.length; i++) {
            var m = src[i] || {}
            var kind = String(m.kind || "")
            var mname = String(m.modelName || "")
            var isCohort = mname.indexOf("Multi-Cohort") >= 0
            if (root.kindFilter === "cohort") { if (!isCohort) continue }
            else if (root.kindFilter === "validated") { if (isCohort || kind === "heuristic") continue }
            else if (root.kindFilter === "heuristic") { if (kind !== "heuristic") continue }
            else if (root.kindFilter !== "All" && kind !== root.kindFilter) continue
            if (root.filterText.length > 0) {
                var hay = (String(m.nameEn || "") + " " + String(m.diseaseKey || "") + " " + mname + " " +
                           String(m.citation || "") + " " + String(m.journal || "") + " " +
                           String(m.articleTitle || "")).toLowerCase()
                if (hay.indexOf(root.filterText) < 0) continue
            }
            out.push(m)
        }
        return out
    }

    // ------------------------------------------------------------------
    // Live results map (current analysis)
    // ------------------------------------------------------------------
    property var liveMap: {
        var map = ({})
        var rows = (backend && backend.riskRows !== undefined && backend.riskRows !== null) ? backend.riskRows : []
        for (var i = 0; i < rows.length; i++) {
            var r = rows[i] || {}
            map[String(r.diseaseKey || "") + "|" + String(r.modelName || "")] = r
        }
        return map
    }

    // ------------------------------------------------------------------
    // Body
    // ------------------------------------------------------------------
    ColumnLayout {
        id: content
        width: Math.min(root.width - 60, 1340)
        anchors.horizontalCenter: parent.horizontalCenter
        y: 28
        spacing: 18

        /* ================= HEADER ================= */
        RowLayout {
            Layout.fillWidth: true
            ColumnLayout {
                spacing: 4
                Text { text: "SCIENTIFIC RISK MODEL LIBRARY"; color: Theme.accent; font.pixelSize: 10; font.bold: true; font.letterSpacing: 2 }
                Text { text: "Risk Models, Weights, Dependencies & References"; color: Theme.text; font.pixelSize: 28; font.bold: true; font.letterSpacing: -0.5 }
                Text {
                    text: "Complete registry of global validated equations and cohort tools with their input dependencies, factor weights and peer-reviewed sources."
                    color: Theme.muted; font.pixelSize: 12; wrapMode: Text.Wrap; Layout.fillWidth: true
                }
            }
            Item { Layout.fillWidth: true }
            Rectangle {
                implicitWidth: totalBadge.implicitWidth + 28; height: 38; radius: 19
                color: "#EFF8FF"; border.color: "#B2DDFF"
                Text { id: totalBadge; anchors.centerIn: parent; text: root.stats.total + " models"; color: "#175CD3"; font.pixelSize: 11; font.bold: true }
            }
        }

        /* ================= STAT CARDS ================= */
        RowLayout {
            Layout.fillWidth: true; spacing: 12
            StatBox { Layout.fillWidth: true; number: root.stats.total;  label: "Total Models";    accent: Theme.accent }
            StatBox { Layout.fillWidth: true; number: root.stats.eq;     label: "Equations";       accent: Theme.violet }
            StatBox { Layout.fillWidth: true; number: root.stats.score;  label: "Scores/Screens";  accent: Theme.success }
            StatBox { Layout.fillWidth: true; number: root.stats.crit;   label: "Criteria/Staging"; accent: Theme.info }
            StatBox { Layout.fillWidth: true; number: root.stats.heur;   label: "Heuristics";      accent: Theme.warning }
            StatBox { Layout.fillWidth: true; number: root.stats.cohort; label: "Cohort Tools";    accent: Theme.danger }
        }

        /* ================= SEARCH + FILTER ================= */
        RowLayout {
            Layout.fillWidth: true; spacing: 10
            TextField {
                id: searchField
                Layout.fillWidth: true; implicitHeight: 44
                placeholderText: "Search model name, disease, citation, journal…"
                color: Theme.text; placeholderTextColor: Theme.muted; selectByMouse: true
                horizontalAlignment: TextInput.AlignLeft
                verticalAlignment: TextInput.AlignVCenter
                leftPadding: 14; rightPadding: riskSearchClearBtn.visible ? 36 : 14
                font.family: Theme.fontFamily
                font.pixelSize: 13
                onTextChanged: root.filterText = text.toLowerCase()
                background: Rectangle { radius: 12; color: Theme.surface; border.color: activeFocus ? Theme.accent : Theme.border }

                ToolButton {
                    id: riskSearchClearBtn
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
                        color: riskSearchClearBtn.hovered ? (Theme.dark ? "#334155" : "#E2E8F0") : "transparent"
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
            ComboBox {
                id: kindBox
                implicitWidth: 190; implicitHeight: 44
                model: ["All kinds", "validated_equation", "validated_score", "validated_criteria",
                        "staging_system", "biomarker_index", "validated_screen", "heuristic", "cohort"]
                onActivated: function(i) { root.kindFilter = (i === 0) ? "All" : currentText }
                background: Rectangle { radius: 12; color: Theme.surface; border.color: Theme.border }
            }
        }

        RowLayout {
            Layout.fillWidth: true; spacing: 10
            Text { text: root.filteredCatalog.length + " of " + root.stats.total + " models shown"; color: Theme.muted; font.pixelSize: 10 }
            Item { Layout.fillWidth: true }
            Text {
                visible: (backend && backend.riskRows ? backend.riskRows.length : 0) > 0
                text: "● Live: " + (backend && backend.riskRows ? backend.riskRows.length : 0) + " evaluated in current analysis"
                color: "#067647"; font.pixelSize: 10; font.bold: true
            }
        }

        /* ================= DISCLAIMER ================= */
        Rectangle {
            Layout.fillWidth: true; implicitHeight: discText.implicitHeight + 26; radius: 12
            color: "#FFFAEB"; border.color: "#FEC84B"
            Text {
                id: discText; anchors.fill: parent; anchors.margins: 13; wrapMode: Text.Wrap
                color: "#8A6100"; font.pixelSize: 11; font.weight: Font.DemiBold
                text: "⚠ Research/educational library. Validated equations embed exact published coefficients; cohort tools show their factor weights. All models carry the validity limits of their source publications. A qualified physician must interpret results."
            }
        }

        /* ================= MODEL CARDS (Repeater — guaranteed render) ================= */
        Repeater {
            model: root.filteredCatalog
            delegate: Rectangle {
                // ✅ بدون required property — فقط modelData محافظت‌شده
                property var md: (modelData !== undefined && modelData !== null) ? modelData : ({})
                property string mName: String(md.modelName || md.nameEn || "—")
                property string dKey: String(md.diseaseKey || "")
                property string kind: String(md.kind || "")
                property real horizon: Number(md.horizonYears || 0)
                property var reqFeats: (md.requiredFeatures !== undefined && md.requiredFeatures !== null) ? md.requiredFeatures : []
                property var wKeys: {
                    var o = (md.weights !== undefined && md.weights !== null) ? md.weights : ({})
                    var ks = []
                    for (var k in o) ks.push(k)
                    return ks
                }
                property var live: root.liveMap[dKey + "|" + String(md.modelName || "")] || null

                Layout.fillWidth: true
                implicitHeight: cardCol.implicitHeight + 32
                radius: 16
                color: Theme.surface
                border.color: Theme.border

                ColumnLayout {
                    id: cardCol
                    anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top
                    anchors.margins: 18
                    spacing: 10

                    /* ===== HEADER ===== */
                    RowLayout {
                        Layout.fillWidth: true; spacing: 10
                        ColumnLayout {
                            Layout.fillWidth: true; spacing: 2
                            Text {
                                text: mName
                                color: Theme.text; font.pixelSize: 15; font.weight: Font.Bold
                                elide: Text.ElideRight; Layout.fillWidth: true
                            }
                            Text {
                                text: String(md.nameEn || "") + "  ·  " + dKey.replace(/_/g, " ")
                                color: Theme.muted; font.pixelSize: 10
                                elide: Text.ElideRight; Layout.fillWidth: true
                            }
                        }
                        Rectangle {
                            visible: kind.length > 0
                            implicitWidth: kindText.implicitWidth + 16; height: 22; radius: 11
                            color: "#F2F4F7"
                            Text { id: kindText; anchors.centerIn: parent; text: kind.replace(/_/g, " "); color: "#667085"; font.pixelSize: 8; font.bold: true }
                        }
                        Rectangle {
                            visible: horizon > 0
                            implicitWidth: horText.implicitWidth + 16; height: 22; radius: 11
                            color: "#EFF8FF"
                            Text { id: horText; anchors.centerIn: parent; text: horizon + "y"; color: "#175CD3"; font.pixelSize: 9; font.bold: true }
                        }
                    }

                    /* ===== LIVE RESULT (after analysis) ===== */
                    Rectangle {
                        visible: live !== null
                        Layout.fillWidth: true
                        implicitHeight: liveText.implicitHeight + 18; radius: 10
                        color: {
                            if (!live || live.status !== "Evaluated") return "#F2F4F7";
                            var lvl = String(live.riskLevel || "").toLowerCase();
                            if (lvl === "critical" || lvl === "very high") return "#FEF3F2";
                            if (lvl === "high") return "#FFFAEB";
                            if (lvl === "moderate") return "#EFF8FF";
                            return "#ECFDF3";
                        }
                        border.color: {
                            if (!live || live.status !== "Evaluated") return Theme.border;
                            var lvl = String(live.riskLevel || "").toLowerCase();
                            if (lvl === "critical" || lvl === "very high") return "#FDA29B";
                            if (lvl === "high") return "#FEDF89";
                            if (lvl === "moderate") return "#B2DDFF";
                            return "#75E0A7";
                        }
                        Text {
                            id: liveText; anchors.fill: parent; anchors.margins: 9
                            text: {
                                if (!live) return "";
                                if (live.status === "Evaluated" || live.status === "Evaluated (Provisional)") {
                                    var pct = Math.round((live.probability || 0) * 100);
                                    var band = live.riskBand || live.riskLevel || "";
                                    var ciStr = "";
                                    if (live.confidence_interval_95) {
                                        var lo = Math.round((live.confidence_interval_95.low || 0) * 100);
                                        var hi = Math.round((live.confidence_interval_95.high || 0) * 100);
                                        ciStr = " [95% CI: " + lo + "%-" + hi + "%]";
                                    }
                                    return "Current analysis: " + live.status + " — " + pct + "% (" + band + ")" + ciStr;
                                }
                                if ((live.missingFeatures || "").length) {
                                    return "Current analysis: " + live.status + " · missing: " + live.missingFeatures;
                                }
                                return "Current analysis: " + live.status;
                            }
                            color: {
                                if (!live || live.status !== "Evaluated") return "#667085";
                                var lvl = String(live.riskLevel || "").toLowerCase();
                                if (lvl === "critical" || lvl === "very high") return "#B42318";
                                if (lvl === "high") return "#B54708";
                                if (lvl === "moderate") return "#175CD3";
                                return "#067647";
                            }
                            font.pixelSize: 10; font.bold: true; wrapMode: Text.Wrap
                        }
                    }

                    /* ===== DEPENDENCIES ===== */
                    ColumnLayout {
                        visible: reqFeats.length > 0
                        Layout.fillWidth: true; spacing: 6
                        Text { text: "DEPENDENCIES (" + reqFeats.length + " required inputs)"; color: Theme.muted; font.pixelSize: 9; font.bold: true; font.letterSpacing: 1.2 }
                        Flow {
                            Layout.fillWidth: true; spacing: 6
                            Repeater {
                                model: reqFeats
                                Rectangle {
                                    height: 22; radius: 11
                                    implicitWidth: depText.implicitWidth + 16
                                    color: "#EFF8FF"; border.color: "#D5E8FF"
                                    Text { id: depText; anchors.centerIn: parent; text: String(modelData); color: "#175CD3"; font.pixelSize: 9 }
                                }
                            }
                        }
                    }

                    /* ===== WEIGHTS ===== */
                    ColumnLayout {
                        visible: wKeys.length > 0
                        Layout.fillWidth: true; spacing: 6
                        Text { text: "MODEL WEIGHTS"; color: Theme.muted; font.pixelSize: 9; font.bold: true; font.letterSpacing: 1.2 }
                        Flow {
                            Layout.fillWidth: true; spacing: 6
                            Repeater {
                                model: wKeys
                                Rectangle {
                                    height: 22; radius: 11
                                    implicitWidth: wText.implicitWidth + 16
                                    color: "#F5F3FF"; border.color: "#E4DEFF"
                                    Text { id: wText; anchors.centerIn: parent; text: String(modelData) + " × " + md.weights[modelData]; color: "#6941C6"; font.pixelSize: 9; font.family: "Consolas" }
                                }
                            }
                        }
                    }

                    /* ===== REFERENCE FOOTER ===== */
                    Rectangle { Layout.fillWidth: true; height: 1; color: Theme.border; opacity: 0.5 }
                    ColumnLayout {
                        Layout.fillWidth: true; spacing: 4
                        Text {
                            visible: String(md.articleTitle || "").length > 0
                            text: "📄 " + md.articleTitle
                            color: Theme.muted; font.pixelSize: 10; font.italic: true
                            wrapMode: Text.Wrap; Layout.fillWidth: true; maximumLineCount: 2; elide: Text.ElideRight
                        }
                        RowLayout {
                            Layout.fillWidth: true; spacing: 8
                            Text {
                                text: {
                                    var c = String(md.citation || "").length > 0 ? md.citation
                                          : (String(md.journal || "").length > 0 ? md.journal : "Scientific Publication")
                                    if (String(md.publicationYear || "").length > 0) c += " (" + md.publicationYear + ")"
                                    return "📖 " + c
                                }
                                color: Theme.muted; font.pixelSize: 10
                                elide: Text.ElideRight; Layout.fillWidth: true
                            }
                            Rectangle {
                                visible: String(md.referenceUrl || "").length > 0 || String(md.doi || "").length > 0 || String(md.pmid || "").length > 0
                                implicitWidth: openText.implicitWidth + 20; height: 26; radius: 13
                                color: openArea.containsMouse ? Theme.accent : "transparent"
                                border.color: Theme.accent; border.width: 1
                                Text { id: openText; anchors.centerIn: parent; text: "Open Paper ↗"; color: openArea.containsMouse ? "#FFFFFF" : Theme.accent; font.pixelSize: 10; font.bold: true }
                                MouseArea {
                                    id: openArea; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                                    onClicked: {
                                        var url = ""
                                        var ref = String(md.referenceUrl || "")
                                        var doi = String(md.doi || "")
                                        var pmid = String(md.pmid || "")
                                        if (ref.length > 0 && ref.indexOf("http") === 0) url = ref
                                        else if (doi.length > 0) url = "https://doi.org/" + doi
                                        else if (pmid.length > 0) url = "https://pubmed.ncbi.nlm.nih.gov/" + pmid + "/"
                                        if (url.length > 0) Qt.openUrlExternally(url)
                                    }
                                }
                            }
                        }
                        RowLayout {
                            visible: String(md.doi || "").length > 0 || String(md.pmid || "").length > 0
                            spacing: 10
                            Text { visible: String(md.doi || "").length > 0; text: "DOI: " + md.doi; color: Theme.violet; font.pixelSize: 9; font.family: "Consolas" }
                            Text { visible: String(md.doi || "").length > 0 && String(md.pmid || "").length > 0; text: "•"; color: Theme.muted; font.pixelSize: 9 }
                            Text { visible: String(md.pmid || "").length > 0; text: "PMID: " + md.pmid; color: Theme.violet; font.pixelSize: 9; font.family: "Consolas" }
                        }
                    }
                }
            }
        }

        /* ================= EMPTY STATE ================= */
        Rectangle {
            visible: root.filteredCatalog.length === 0
            Layout.fillWidth: true; implicitHeight: 110; radius: 16
            color: Theme.surfaceAlt; border.color: Theme.border
            Column {
                anchors.centerIn: parent; spacing: 8
                Text { anchors.horizontalCenter: parent.horizontalCenter; text: "🔍"; font.pixelSize: 30 }
                Text { anchors.horizontalCenter: parent.horizontalCenter; text: "No model matches your search/filter."; color: Theme.muted; font.pixelSize: 12 }
                HgButton {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: "Clear filters"
                    onClicked: { searchField.text = ""; root.filterText = ""; kindBox.currentIndex = 0; root.kindFilter = "All" }
                }
            }
        }

        Item { Layout.preferredHeight: 20 }
    }

    // ------------------------------------------------------------------
    // Components
    // ------------------------------------------------------------------
    component StatBox: HgCard {
        property int number: 0
        property string label: ""
        property color accent: Theme.accent
        implicitHeight: 78
        Column {
            anchors.centerIn: parent; spacing: 3
            Text { anchors.horizontalCenter: parent.horizontalCenter; text: number; color: accent; font.pixelSize: 22; font.bold: true }
            Text { anchors.horizontalCenter: parent.horizontalCenter; text: label; color: Theme.muted; font.pixelSize: 9; font.weight: Font.DemiBold }
        }
    }
}
