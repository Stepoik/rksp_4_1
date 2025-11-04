import org.json.JSONArray
import org.json.JSONObject
import java.io.File

fun main() {
    val text = File("data.json").readText()
    val json = JSONObject(text)

    // Читаем "conditions"
    val conditionsArray = json.getJSONArray("conditions")
    val conditions = mutableListOf<Map<String, Any?>>()
    for (i in 0 until conditionsArray.length()) {
        val obj = conditionsArray.getJSONObject(i)
        val item = mapOf(
            "field" to obj.getString("field"),
            "condition" to obj.getString("condition"),
            "value" to obj.get("value")
        )
        conditions.add(item)
    }

    // Читаем "participants"
    val participantsArray = json.getJSONArray("participants")
    val participants = mutableListOf<Map<String, Any?>>()
    for (i in 0 until participantsArray.length()) {
        val obj = participantsArray.getJSONObject(i)
        val item = mapOf(
            "id" to obj.getInt("id"),
            "first_name" to obj.getString("first_name"),
            "last_name" to obj.getString("last_name"),
            "email" to obj.getString("email"),
            "gender" to obj.getString("gender"),
            "shirt_size" to obj.getString("shirt_size"),
            "age" to obj.getInt("age"),
            "level" to obj.getString("level"),
            "language" to obj.getString("language"),
            "country_from" to obj.getString("country_from"),
            "was_participant_count" to obj.getInt("was_participant_count")
        )
        participants.add(item)
    }

    println("Conditions:")
    conditions.forEach { println(it) }

    println("\nParticipants:")
    participants.forEach { println(it) }
}
