import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Popup {
    id: root
    objectName: 'aiInstructionDialog'

    property bool batchMode: false
    property int observationId: 0
    property string instructionText: ''

    parent: Overlay.overlay
    anchors.centerIn: parent
    width: Math.min(620, parent ? parent.width - 32 : 620)
    height: Math.min(680, parent ? parent.height - 32 : 680)
    modal: true
    focus: true
    padding: 0
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

    function refreshInstruction() {
        instructionText = batchMode
            ? Observations.buildSelectedAiInstructions(
                instructionMode.currentIndex === 0 ? 'combined' : 'individual'
            )
            : Observations.aiInstructionForObservation(observationId)
    }

    function openForObservation(id) {
        batchMode = false
        observationId = id
        instructionMode.currentIndex = 0
        refreshInstruction()
        open()
    }

    function openForSelection() {
        batchMode = true
        observationId = 0
        instructionMode.currentIndex = 0
        refreshInstruction()
        open()
    }

    background: Rectangle {
        color: Theme.surfaceRaised
        border.color: Theme.borderStrong
        border.width: 1
        radius: 16
    }

    contentItem: ColumnLayout {
        spacing: 12

        RowLayout {
            Layout.fillWidth: true
            Layout.leftMargin: 20
            Layout.rightMargin: 16
            Layout.topMargin: 18
            spacing: 12

            Rectangle {
                Layout.preferredWidth: 36
                Layout.preferredHeight: 36
                radius: 10
                color: Theme.surfaceAlt
                border.color: Theme.border

                InspyredIcon {
                    anchors.centerIn: parent
                    width: 20
                    height: 20
                    name: 'sparkle'
                    color: Theme.cyan
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2

                Text {
                    text: 'AI coding instruction'
                    color: Theme.textPrimary
                    font.pixelSize: 18
                    font.weight: Font.DemiBold
                }

                Text {
                    text: batchMode
                        ? Observations.selectedCount + ' selected note(s) in one project'
                        : 'Generated from one captured observation'
                    color: Theme.textSecondary
                    font.pixelSize: 12
                }
            }

            InspyredButton {
                iconName: 'close'
                iconOnly: true
                text: 'Close'
                compact: true
                tooltip: 'Close'
                onClicked: root.close()
            }
        }

        InspyredComboBox {
            id: instructionMode
            visible: root.batchMode && Observations.selectedCount > 1
            Layout.fillWidth: true
            Layout.leftMargin: 20
            Layout.rightMargin: 20
            model: ['One combined instruction', 'Separate instructions']
            onActivated: root.refreshInstruction()
        }

        TextArea {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.leftMargin: 20
            Layout.rightMargin: 20
            text: root.instructionText
            readOnly: true
            selectByMouse: true
            wrapMode: TextEdit.Wrap
            color: Theme.textPrimary
            selectionColor: Theme.accent
            selectedTextColor: '#FFFFFF'
            font.pixelSize: 13
            leftPadding: 14
            rightPadding: 14
            topPadding: 12
            bottomPadding: 12

            background: Rectangle {
                color: Theme.surface
                border.color: Theme.border
                radius: 11
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.leftMargin: 20
            Layout.rightMargin: 20
            Layout.bottomMargin: 18
            spacing: 10

            Text {
                Layout.fillWidth: true
                text: 'Review the instruction before giving it to a coding agent.'
                color: Theme.textSecondary
                font.pixelSize: 11
                wrapMode: Text.Wrap
            }

            InspyredButton {
                text: 'Close'
                forceLabel: true
                compact: true
                onClicked: root.close()
            }

            InspyredButton {
                text: 'Copy instruction'
                forceLabel: true
                compact: true
                accent: true
                enabled: root.instructionText.length > 0
                onClicked: Observations.copyText(root.instructionText)
            }
        }
    }
}
