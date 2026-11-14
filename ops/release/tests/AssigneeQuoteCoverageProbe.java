import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import cn.jia.agent.entity.AssigneeRecommendation.Workload;
import cn.jia.economy.mapper.EconomyPriceCatalogMapper;
import cn.jia.economy.pricing.*;
import cn.jia.economy.service.EconomyScope;
import cn.jia.economy.service.impl.DatabaseTaskPricingService;
import org.mybatis.spring.SqlSessionFactoryBean;
import org.mybatis.spring.SqlSessionTemplate;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.DriverManagerDataSource;
import org.springframework.jdbc.datasource.DataSourceTransactionManager;
import org.springframework.transaction.TransactionDefinition;
import org.springframework.transaction.support.TransactionTemplate;
import tools.jackson.databind.JsonNode;
import tools.jackson.databind.ObjectMapper;

/** Read-only coverage using the candidate/installed JAR's exact classes, never billing.quote.
 * Arguments are private file paths: datasource properties, scope-baseline.json, price-baseline.json.
 * No full application startup, provider calls, quote IDs, wallet or binding writes.
 */
class AssigneeQuoteCoverageProbe {
    private static final ObjectMapper JSON = new ObjectMapper();
    private static void check(boolean valid, String message) { if (!valid) throw new AssertionError(message); }
    private static String required(Properties properties, String key) {
        String value = properties.getProperty(key);
        check(value != null && !value.isBlank() && !value.contains("${"), "Unresolved datasource setting: " + key);
        return value;
    }
    private static void quote(DatabaseTaskPricingService prices, EconomyScope scope, String model,
                              Map<String, JsonNode> expected, Map<String, Integer> failures, int[] counters) {
        var baseline = model == null ? null : expected.get(model);
        if (baseline == null) { failures.merge(model == null || model.isBlank() ? "MODEL_NOT_REPORTED" : "MODEL_NOT_IN_FROZEN_BASELINE", 1, Integer::sum); return; }
        for (var kind : Workload.Kind.values()) {
            var test = baseline.get("acceptanceCase");
            var work = new TaskWorkload(kind.name(), test.get("inputTokens").longValue(), test.get("outputTokens").longValue(),
                    test.get("deliverables").longValue(), Map.of());
            try {
                var ready = prices.prepare(scope, work, model);
                var actual = TaskQuoteCalculator.calculate(ready.estimate(), ready.modelPrice(), ready.toolPrices());
                check(actual.amountWen() == test.get("expectedWen").longValue(), "Frozen expected quotation mismatch");
                check(ready.modelPrice().channel().equals(baseline.get("channel").asString()), "Unexpected quote channel");
                check(ready.modelPrice().tier().equals(baseline.get("tier").asString()), "Unexpected quote tier");
                check(ready.modelPrice().version().equals(baseline.get("priceVersion").asString()), "Unexpected quote version");
                check(ready.toolPrices().isEmpty() && ready.workload().toolUnits().isEmpty(), "Unexpected paid tools");
                counters[2]++;
            } catch (TaskPricingService.Unavailable failure) { failures.merge(failure.reason().name(), 1, Integer::sum); }
        }
    }
    public static void main(String[] args) throws Exception {
        check(args.length == 3, "Expected private datasource, scope and frozen baseline file paths");
        var properties = new Properties();
        try (var input = Files.newBufferedReader(Path.of(args[0]), StandardCharsets.UTF_8)) { properties.load(input); }
        var source = new DriverManagerDataSource(required(properties, "spring.datasource.url"),
                required(properties, "spring.datasource.username"), Objects.requireNonNull(properties.getProperty("spring.datasource.password"), "Explicit datasource password setting required"));
        var jdbc = new JdbcTemplate(source);
        var configuration = new org.apache.ibatis.session.Configuration();
        configuration.setMapUnderscoreToCamelCase(true); configuration.addMapper(EconomyPriceCatalogMapper.class);
        var factory = new SqlSessionFactoryBean(); factory.setDataSource(source); factory.setConfiguration(configuration);
        var prices = new DatabaseTaskPricingService(new SqlSessionTemplate(factory.getObject()).getMapper(EconomyPriceCatalogMapper.class), JSON);
        var manager = new DataSourceTransactionManager(source);
        var tx = new TransactionTemplate(manager); tx.setReadOnly(true);
        tx.setIsolationLevel(TransactionDefinition.ISOLATION_REPEATABLE_READ);
        var scopes = JSON.readTree(Files.readString(Path.of(args[1]))).get("scopes");
        var expected = new LinkedHashMap<String, JsonNode>();
        for (var row : JSON.readTree(Files.readString(Path.of(args[2]))).get("prices"))
            check(expected.putIfAbsent(row.get("model").asString(), row) == null, "Duplicate baseline model");
        check(!expected.isEmpty() && scopes.isArray() && !scopes.isEmpty(), "Empty coverage baseline");
        var failures = new TreeMap<String, Integer>(); var counts = new int[3];
        // Connector/J propagates setReadOnly to the server; verify it before catalog reads.
        tx.executeWithoutResult(status -> {
            check(Integer.valueOf(1).equals(jdbc.queryForObject("SELECT @@session.transaction_read_only", Integer.class)),
                    "Server transaction must be read-only");
            for (var entry : scopes) {
                var scope = new EconomyScope(entry.get("tenantId").asString(), entry.get("clientId").asString());
                var bound = jdbc.queryForList("""
                        SELECT r.execution_model FROM agent_persona_binding b
                        LEFT JOIN agent_runtime r ON r.tenant_id=b.tenant_id AND r.client_id=b.client_id
                          AND r.agent_id=b.agent_id AND r.binding_id=b.id
                        WHERE b.tenant_id=? AND b.client_id=? AND b.status=1
                        """, String.class, scope.tenantId(), scope.clientId());
                counts[0] += bound.size();
                for (var model : bound) quote(prices, scope, model, expected, failures, counts);
                var models = jdbc.queryForList("SELECT DISTINCT model_id FROM agent_persona_model WHERE tenant_id=? AND client_id=?",
                        String.class, scope.tenantId(), scope.clientId());
                check(new HashSet<>(models).equals(expected.keySet()), "Supported model set drifted from frozen baseline");
                counts[1] += models.size();
                for (var model : models) quote(prices, scope, model, expected, failures, counts);
            }
        });
        System.out.println(JSON.writeValueAsString(Map.of("activeBindings", counts[0], "supportedModels", counts[1],
                "quotations", counts[2], "kinds", Workload.Kind.values().length, "failures", failures,
                "readOnly", true, "result", failures.isEmpty() ? "PASS" : "FAIL")));
        check(failures.isEmpty(), "Quote coverage incomplete; see sanitized failure counts");
    }
}
