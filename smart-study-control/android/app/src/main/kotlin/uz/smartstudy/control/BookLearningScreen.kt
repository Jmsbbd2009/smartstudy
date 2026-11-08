package uz.smartstudy.control

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import kotlinx.serialization.json.*
import uz.smartstudy.data.StudyData

private suspend fun cachedLearning(repository:StudyData,path:String,list:Boolean=false):Pair<JsonElement,Boolean> {
    val user=repository.vault.userId()
    return try {
        val value:JsonElement=if(list) JsonArray(repository.api.list(path)) else repository.api.get(path)
        check(repository.vault.userId()==user)
        if(value.toString().length<=2_000_000)repository.cacheLearning(path,value.toString());value to false
    } catch(e:Exception) {
        if(e is kotlinx.coroutines.CancellationException)throw e
        if(e is retrofit2.HttpException && e.code() in listOf(401,403,404))throw e
        check(repository.vault.userId()==user)
        val cached=repository.learning(path) ?: throw e
        Json.parseToJsonElement(cached) to true
    }
}
@Composable fun BookLearningScreen(vm:StudyViewModel) {
    var plans by remember {mutableStateOf<List<JsonObject>>(emptyList())}
    var plan by remember {mutableStateOf<JsonObject?>(null)}
    var source by remember {mutableStateOf<JsonObject?>(null)}
    var lesson by remember {mutableStateOf<JsonObject?>(null)}
    var attempt by remember {mutableStateOf<JsonObject?>(null)}
    var page by remember {mutableIntStateOf(1)}
    var offline by remember {mutableStateOf(false)}
    val answers=remember {mutableStateMapOf<String,Int>()}
    val student=vm.user?.text("role")=="STUDENT"
    fun loadPage(number:Int){
        val selected=plan ?: return
        page=number
        vm.run {val result=cachedLearning(vm.repository,"books/${selected.text("book_id")}/pages/$number");source=result.first.jsonObject;offline=result.second}
    }
    fun loadPlan(id:String){vm.run {
        val result=cachedLearning(vm.repository,"reading/plans/$id");plan=result.first.jsonObject;offline=result.second
        page=plan!!.text("start_page").toInt();lesson=null;attempt=null;answers.clear()
        val initial=cachedLearning(vm.repository,"books/${plan!!.text("book_id")}/pages/$page");source=initial.first.jsonObject;offline=offline||initial.second
    }}
    LaunchedEffect(Unit){vm.run {val result=cachedLearning(vm.repository,"reading/plans",true);plans=result.first.jsonArray.map {it.jsonObject};offline=result.second}}
    Page(R.string.books) {
        if(offline)Text(stringResource(R.string.reading_offline),color=MaterialTheme.colorScheme.secondary)
        Text(stringResource(R.string.reading_notice))
        if(plan==null) {
            if(plans.isEmpty())Text(stringResource(R.string.empty))
            plans.forEach {p->OutlinedButton(onClick={loadPlan(p.text("id"))},modifier=Modifier.fillMaxWidth().heightIn(min=60.dp)) {
                Column {Text(p.text("book_title"));Text("${p.text("start_page")}–${p.text("end_page")} "+stringResource(R.string.reading_page_label))}
            }}
        } else {
            val selected=plan!!
            if(attempt?.text("status")!="ACTIVE") {
            Text(selected.text("book_title"),style=MaterialTheme.typography.headlineMedium)
            Action(R.string.back){plan=null;source=null;lesson=null;attempt=null}
            selected["progress"]?.jsonObject?.let {p->
                Text(stringResource(R.string.reading_self_reported)+": "+p.text("self_reported_percent")+"%")
                LinearProgressIndicator(progress={(p.text("self_reported_percent").toFloatOrNull()?:0f)/100},modifier=Modifier.fillMaxWidth())
                Text(stringResource(R.string.reading_checked)+": "+p.text("checked_percent")+"%")
                LinearProgressIndicator(progress={(p.text("checked_percent").toFloatOrNull()?:0f)/100},modifier=Modifier.fillMaxWidth(),color=MaterialTheme.colorScheme.secondary)
            }
            Text("$page "+stringResource(R.string.reading_page_label),style=MaterialTheme.typography.titleLarge)
            Card(Modifier.fillMaxWidth()){SelectionContainerText(source?.text("text").orEmpty())}
            Row(horizontalArrangement=Arrangement.spacedBy(10.dp)) {
                OutlinedButton(onClick={loadPage(page-1)},enabled=page>selected.text("start_page").toInt()){Text(stringResource(R.string.previous_page))}
                OutlinedButton(onClick={loadPage(page+1)},enabled=page<selected.text("end_page").toInt()){Text(stringResource(R.string.next_page))}
            }
            if(student)Action(R.string.mark_page){vm.run {
                vm.repository.api.post("reading/plans/${selected.text("id")}/progress",buildJsonObject {put("page_number",page);put("reported_seconds",0)})
                plan=vm.repository.api.get("reading/plans/${selected.text("id")}");vm.repository.cacheLearning("reading/plans/${selected.text("id")}",plan.toString())
            }}
            Text(stringResource(R.string.concepts),style=MaterialTheme.typography.titleLarge)
            selected["lessons"]?.jsonArray?.forEach {value->val l=value.jsonObject
                OutlinedButton(onClick={vm.run {val result=cachedLearning(vm.repository,"reading/lessons/${l.text("id")}");lesson=result.first.jsonObject;offline=result.second;attempt=null;answers.clear()}},modifier=Modifier.fillMaxWidth()){Text(l.text("title"))}
            }
            lesson?.let {material->
                val content=material["content"]!!.jsonObject
                Text(content.text("title"),style=MaterialTheme.typography.headlineSmall)
                Text(content.text("summary"))
                val expanded=remember(material.text("id")){mutableStateMapOf<String,Boolean>()}
                content["concepts"]?.jsonArray?.forEach {value->val c=value.jsonObject;val id=c.text("id")
                    Card(onClick={expanded[id]=expanded[id]!=true},modifier=Modifier.fillMaxWidth()) {
                        Column(Modifier.padding(18.dp),verticalArrangement=Arrangement.spacedBy(10.dp)) {
                            Text(c.text("title"),style=MaterialTheme.typography.titleMedium)
                            Text(c.text("source_page")+" "+stringResource(R.string.reading_page_label))
                            if(expanded[id]==true){Text(c.text("explanation"));Text(c.text("source_quote"),style=MaterialTheme.typography.bodySmall)}
                        }
                    }
                }
                if(student && attempt==null)Action(R.string.start_reading_test){vm.run {
                    attempt=vm.repository.api.post("reading/plans/${selected.text("id")}/lessons/${material.text("id")}/attempts",buildJsonObject {},java.util.UUID.randomUUID().toString());answers.clear()
                }}
            }
            }
            attempt?.let {test->
                if(test.text("status")=="ACTIVE") {
                    Text("Bilimni tekshirish · Test tugaguncha AI yordami yopilgan",style=MaterialTheme.typography.titleMedium)
                    test["questions"]!!.jsonArray.forEach {value->val question=value.jsonObject
                        Text(question.text("prompt"),style=MaterialTheme.typography.titleMedium)
                        question["options"]!!.jsonArray.forEachIndexed {index,option->
                            Row {RadioButton(selected=answers[question.text("id")]==index,onClick={answers[question.text("id")]=index});Text(option.jsonPrimitive.content,modifier=Modifier.padding(top=12.dp))}
                        }
                    }
                    Action(R.string.finish_reading_test,answers.size==test["questions"]!!.jsonArray.size){vm.run {
                        attempt=vm.repository.api.post("reading/attempts/${test.text("id")}/finish",buildJsonObject {put("answers",buildJsonObject {answers.forEach {(key,value)->put(key,value)}})})
                        plan=vm.repository.api.get("reading/plans/${selected.text("id")}");vm.repository.cacheLearning("reading/plans/${selected.text("id")}",plan.toString())
                    }}
                } else {
                    val result=test["result"]!!.jsonObject
                    Text(result.text("percent")+"%",style=MaterialTheme.typography.displayLarge)
                    val reward=result["reward"]!!.jsonObject
                    Text(stringResource(if(reward.text("state")=="GRANTED") R.string.reading_granted else if(reward.text("state")=="ALREADY_GRANTED") R.string.reading_already else if(result["passed"]!!.jsonPrimitive.boolean) R.string.reading_adult_required else R.string.reading_practice))
                    Text(reward.text("minutes")+" "+stringResource(R.string.minutes))
                    test["review"]?.jsonArray?.forEach {Text(it.jsonObject.text("explanation"))}
                }
            }
        }
    }
}
