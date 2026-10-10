import QtQuick

Item {
    id: root

    property string name: ''
    property color color: '#FFFFFF'
    property real strokeWidth: 1.8

    implicitWidth: 20
    implicitHeight: 20

    Canvas {
        id: canvas
        anchors.fill: parent
        antialiasing: true

        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()

        onPaint: {
            const ctx = getContext('2d')
            function circle(cx, cy, radius) {
                const k = radius * 0.55228475
                ctx.moveTo(cx + radius, cy)
                ctx.bezierCurveTo(cx + radius, cy + k, cx + k, cy + radius, cx, cy + radius)
                ctx.bezierCurveTo(cx - k, cy + radius, cx - radius, cy + k, cx - radius, cy)
                ctx.bezierCurveTo(cx - radius, cy - k, cx - k, cy - radius, cx, cy - radius)
                ctx.bezierCurveTo(cx + k, cy - radius, cx + radius, cy - k, cx + radius, cy)
            }

            ctx.clearRect(0, 0, width, height)
            ctx.save()
            ctx.scale(width / 24, height / 24)
            ctx.strokeStyle = root.color
            ctx.fillStyle = root.color
            ctx.lineWidth = root.strokeWidth
            ctx.lineCap = 'round'
            ctx.lineJoin = 'round'

            ctx.beginPath()

            switch (root.name) {
            case 'inbox':
                ctx.moveTo(4.5, 5.5)
                ctx.lineTo(19.5, 5.5)
                ctx.lineTo(19.5, 18.5)
                ctx.lineTo(4.5, 18.5)
                ctx.lineTo(4.5, 5.5)
                ctx.moveTo(4.5, 13)
                ctx.lineTo(9, 13)
                ctx.lineTo(10.5, 15)
                ctx.lineTo(13.5, 15)
                ctx.lineTo(15, 13)
                ctx.lineTo(19.5, 13)
                break
            case 'layers':
                ctx.moveTo(4, 8)
                ctx.lineTo(12, 3.5)
                ctx.lineTo(20, 8)
                ctx.lineTo(12, 12.5)
                ctx.lineTo(4, 8)
                ctx.moveTo(4, 12)
                ctx.lineTo(12, 16.5)
                ctx.lineTo(20, 12)
                ctx.moveTo(4, 16)
                ctx.lineTo(12, 20.5)
                ctx.lineTo(20, 16)
                break
            case 'progress':
                ctx.moveTo(18.7, 8.4)
                ctx.bezierCurveTo(17.2, 4.9, 13.1, 3.2, 9.3, 4.5)
                ctx.bezierCurveTo(5.5, 5.8, 3.5, 9.9, 4.6, 13.8)
                ctx.bezierCurveTo(5.7, 17.7, 9.7, 20.1, 13.7, 19.2)
                ctx.bezierCurveTo(16.2, 18.7, 18.2, 17, 19.2, 14.8)
                ctx.moveTo(18.7, 8.4)
                ctx.lineTo(19.5, 4.8)
                ctx.lineTo(15.9, 5.6)
                break
            case 'verify':
                circle(12, 12, 8)
                ctx.moveTo(8.2, 12.1)
                ctx.lineTo(10.7, 14.6)
                ctx.lineTo(15.9, 9.3)
                break
            case 'settings':
                circle(12, 12, 5.5)
                ctx.moveTo(12, 2.5); ctx.lineTo(12, 5)
                ctx.moveTo(12, 19); ctx.lineTo(12, 21.5)
                ctx.moveTo(2.5, 12); ctx.lineTo(5, 12)
                ctx.moveTo(19, 12); ctx.lineTo(21.5, 12)
                ctx.moveTo(5.3, 5.3); ctx.lineTo(7.1, 7.1)
                ctx.moveTo(16.9, 16.9); ctx.lineTo(18.7, 18.7)
                ctx.moveTo(18.7, 5.3); ctx.lineTo(16.9, 7.1)
                ctx.moveTo(7.1, 16.9); ctx.lineTo(5.3, 18.7)
                circle(12, 12, 2.3)
                break
            case 'add':
                ctx.moveTo(12, 5)
                ctx.lineTo(12, 19)
                ctx.moveTo(5, 12)
                ctx.lineTo(19, 12)
                break
            case 'sparkle':
                ctx.moveTo(12, 3.5)
                ctx.bezierCurveTo(12.7, 8.2, 14.8, 10.3, 19.5, 11)
                ctx.bezierCurveTo(14.8, 11.7, 12.7, 13.8, 12, 18.5)
                ctx.bezierCurveTo(11.3, 13.8, 9.2, 11.7, 4.5, 11)
                ctx.bezierCurveTo(9.2, 10.3, 11.3, 8.2, 12, 3.5)
                ctx.moveTo(19, 3.5)
                ctx.lineTo(19, 7.5)
                ctx.moveTo(17, 5.5)
                ctx.lineTo(21, 5.5)
                break
            case 'close':
                ctx.moveTo(6.5, 6.5)
                ctx.lineTo(17.5, 17.5)
                ctx.moveTo(17.5, 6.5)
                ctx.lineTo(6.5, 17.5)
                break
            case 'minimize':
                ctx.moveTo(6, 12)
                ctx.lineTo(18, 12)
                break
            case 'maximize':
                ctx.moveTo(6, 6)
                ctx.lineTo(18, 6)
                ctx.lineTo(18, 18)
                ctx.lineTo(6, 18)
                ctx.lineTo(6, 6)
                break
            case 'restore':
                ctx.moveTo(5, 8)
                ctx.lineTo(16, 8)
                ctx.lineTo(16, 19)
                ctx.lineTo(5, 19)
                ctx.lineTo(5, 8)
                ctx.moveTo(8, 8)
                ctx.lineTo(8, 5)
                ctx.lineTo(19, 5)
                ctx.lineTo(19, 16)
                ctx.lineTo(16, 16)
                break
            }

            ctx.stroke()
            ctx.restore()
        }
    }

    onNameChanged: canvas.requestPaint()
    onColorChanged: canvas.requestPaint()
    onStrokeWidthChanged: canvas.requestPaint()
}
