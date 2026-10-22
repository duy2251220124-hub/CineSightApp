import os

def format_room(content):
    content = content.replace(
        "final roomId = room['room_id'] ?? 'Unknown';",
        "final rawRoomId = room['room_id'] ?? 'Unknown';\n                  final roomId = rawRoomId.startsWith('seats_config_room') ? 'Phòng chiếu ' + rawRoomId.replaceAll('seats_config_room', '') : rawRoomId;"
    )
    return content

with open('lib/features/rooms/presentation/cs_rooms_screen.dart', 'r', encoding='utf-8') as f:
    c = f.read()
c = format_room(c)
with open('lib/features/rooms/presentation/cs_rooms_screen.dart', 'w', encoding='utf-8') as f:
    f.write(c)

with open('lib/features/rooms/presentation/cs_seat_map_screen.dart', 'r', encoding='utf-8') as f:
    c = f.read()
c = c.replace("title: 'Sơ đồ ghế - ${widget.roomId}',", "title: 'Sơ đồ ghế - ${widget.roomId.startsWith('seats_config_room') ? \"Phòng chiếu \" + widget.roomId.replaceAll('seats_config_room', '') : widget.roomId}',")
c = c.replace("_selectedSeats.isEmpty ? null : () {", "() {")
c = c.replace("_selectedSeats.isEmpty ? 'Báo ghế hư' : 'Báo ghế hư (${_selectedSeats.length} ghế)'", "'Báo ghế hư'")
# remove selection mode from cs_seat_map in cs_seat_map_screen
c = c.replace("selectionMode: true,", "selectionMode: false,")

with open('lib/features/rooms/presentation/cs_seat_map_screen.dart', 'w', encoding='utf-8') as f:
    f.write(c)
print("Done fix9")
