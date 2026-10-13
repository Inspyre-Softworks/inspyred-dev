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
            let fillShape = false

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
            case 'refresh':
                ctx.moveTo(19, 8.5)
                ctx.bezierCurveTo(17.5, 5.1, 13.6, 3.4, 9.9, 4.4)
                ctx.bezierCurveTo(6.1, 5.4, 3.7, 9.1, 4.3, 13)
                ctx.bezierCurveTo(4.9, 16.9, 8.3, 19.7, 12.3, 19.6)
                ctx.bezierCurveTo(15.2, 19.5, 17.8, 17.8, 19.1, 15.3)
                ctx.moveTo(19, 8.5)
                ctx.lineTo(19.8, 4.8)
                ctx.lineTo(16.1, 5.7)
                break
            case 'verify':
                circle(12, 12, 8)
                ctx.moveTo(8.2, 12.1)
                ctx.lineTo(10.7, 14.6)
                ctx.lineTo(15.9, 9.3)
                break
            case 'select':
                ctx.moveTo(5.5, 5.5)
                ctx.lineTo(18.5, 5.5)
                ctx.lineTo(18.5, 18.5)
                ctx.lineTo(5.5, 18.5)
                ctx.lineTo(5.5, 5.5)
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
            case 'info':
                circle(12, 12, 8.5)
                ctx.moveTo(12, 10.5)
                ctx.lineTo(12, 17)
                ctx.moveTo(12, 7)
                ctx.lineTo(12, 7.1)
                break
            case 'add':
                ctx.moveTo(12, 5)
                ctx.lineTo(12, 19)
                ctx.moveTo(5, 12)
                ctx.lineTo(19, 12)
                break
            case 'edit':
                ctx.moveTo(5, 19)
                ctx.lineTo(8.5, 18.2)
                ctx.lineTo(18.4, 8.3)
                ctx.lineTo(15.7, 5.6)
                ctx.lineTo(5.8, 15.5)
                ctx.lineTo(5, 19)
                ctx.moveTo(14.4, 6.9)
                ctx.lineTo(17.1, 9.6)
                break
            case 'trash':
                ctx.moveTo(5.5, 7)
                ctx.lineTo(18.5, 7)
                ctx.moveTo(9, 7)
                ctx.lineTo(9.8, 4.5)
                ctx.lineTo(14.2, 4.5)
                ctx.lineTo(15, 7)
                ctx.moveTo(7.2, 7)
                ctx.lineTo(8.2, 20)
                ctx.lineTo(15.8, 20)
                ctx.lineTo(16.8, 7)
                ctx.moveTo(10.2, 10)
                ctx.lineTo(10.6, 17)
                ctx.moveTo(13.8, 10)
                ctx.lineTo(13.4, 17)
                break
            case 'archive':
                ctx.moveTo(4.5, 7.5)
                ctx.lineTo(19.5, 7.5)
                ctx.lineTo(18.2, 20)
                ctx.lineTo(5.8, 20)
                ctx.lineTo(4.5, 7.5)
                ctx.moveTo(4, 4)
                ctx.lineTo(20, 4)
                ctx.lineTo(20, 7.5)
                ctx.lineTo(4, 7.5)
                ctx.lineTo(4, 4)
                ctx.moveTo(9.5, 12)
                ctx.lineTo(14.5, 12)
                break
            case 'arrow-up':
                ctx.moveTo(12, 19)
                ctx.lineTo(12, 5)
                ctx.moveTo(6.5, 10.5)
                ctx.lineTo(12, 5)
                ctx.lineTo(17.5, 10.5)
                break
            case 'arrow-down':
                ctx.moveTo(12, 5)
                ctx.lineTo(12, 19)
                ctx.moveTo(6.5, 13.5)
                ctx.lineTo(12, 19)
                ctx.lineTo(17.5, 13.5)
                break
            case 'external':
                ctx.moveTo(13, 5)
                ctx.lineTo(19, 5)
                ctx.lineTo(19, 11)
                ctx.moveTo(19, 5)
                ctx.lineTo(10.5, 13.5)
                ctx.moveTo(16.5, 13)
                ctx.lineTo(16.5, 18.5)
                ctx.lineTo(5.5, 18.5)
                ctx.lineTo(5.5, 7.5)
                ctx.lineTo(11, 7.5)
                break
            case 'github':
                fillShape = true
                ctx.moveTo(5.2, 9.2)
                ctx.lineTo(4.7, 5.1)
                ctx.lineTo(8.5, 6.8)
                ctx.bezierCurveTo(10.8, 5.9, 13.2, 5.9, 15.5, 6.8)
                ctx.lineTo(19.3, 5.1)
                ctx.lineTo(18.8, 9.2)
                ctx.bezierCurveTo(19.6, 10.3, 20, 11.6, 20, 13)
                ctx.bezierCurveTo(20, 16.2, 18.1, 18, 14.6, 18.5)
                ctx.bezierCurveTo(15.1, 19, 15.3, 19.8, 15.3, 21)
                ctx.lineTo(8.8, 21)
                ctx.lineTo(8.8, 18.6)
                ctx.bezierCurveTo(6.3, 18.3, 5.7, 17.2, 5.2, 16.2)
                ctx.bezierCurveTo(4.8, 15.4, 4.2, 14.9, 3.4, 14.9)
                ctx.bezierCurveTo(2.8, 14.9, 2.5, 14.4, 3.3, 14.2)
                ctx.bezierCurveTo(4.8, 13.8, 5.7, 15, 6.3, 16)
                ctx.bezierCurveTo(6.8, 16.8, 7.6, 17, 8.8, 16.8)
                ctx.bezierCurveTo(5.7, 16.2, 4, 14.4, 4, 11.9)
                ctx.bezierCurveTo(4, 10.9, 4.4, 10, 5.2, 9.2)
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

            if (fillShape)
                ctx.fill()
            else
                ctx.stroke()
            ctx.restore()
        }
    }

    onNameChanged: canvas.requestPaint()
    onColorChanged: canvas.requestPaint()
    onStrokeWidthChanged: canvas.requestPaint()
}
