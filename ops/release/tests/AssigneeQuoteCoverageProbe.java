import java.math.BigDecimal;
import java.nio.file.*;
import java.util.*;
import org.springframework.boot.context.properties.bind.*;
import org.springframework.boot.context.properties.source.*;
import cn.jia.agent.entity.AssigneeRecommendation.Workload;
import cn.jia.agent.service.recommendation.AssigneeQuoteRoutes;
import cn.jia.economy.config.EconomyPricingProperties;
import cn.jia.economy.pricing.*;
import cn.jia.economy.service.impl.ConfiguredTaskPricingService;

/** Read-only beta configuration regression, using the installed JAR's actual classes.
 * java -cp '<extracted-production-libs>/*' AssigneeQuoteCoverageProbe.java candidate.properties
 * No Spring application, database, provider, assignment, or wallet writes are started.
 */
class AssigneeQuoteCoverageProbe {
    static Binder binder(Properties properties) {
        var values = new HashMap<String, Object>();
        properties.forEach((key, value) -> values.put(key.toString(), value));
        return new Binder(new MapConfigurationPropertySource(values));
    }
    static ConfiguredTaskPricingService catalog(Properties properties) {
        return new ConfiguredTaskPricingService(binder(properties)
                .bind("economy.pricing", Bindable.of(EconomyPricingProperties.class)).get());
    }
    static long amount(ConfiguredTaskPricingService catalog, TaskWorkload work, TaskPricingService.ModelKey key) {
        var ready = catalog.prepare(work, key);
        return TaskQuoteCalculator.calculate(ready.estimate(), ready.modelPrice(), ready.toolPrices()).amountWen();
    }
    static void check(boolean valid, String message) { if (!valid) throw new AssertionError(message); }
    static void unavailable(Runnable action, TaskPricingService.Unavailable.Reason reason) {
        try { action.run(); throw new AssertionError("Missing expected " + reason); }
        catch (TaskPricingService.Unavailable failure) { check(failure.reason() == reason, "Wrong unavailable reason"); }
    }
    public static void main(String[] args) throws Exception {
        var properties = new Properties();
        try (var input = Files.newInputStream(Path.of(args[0]))) { properties.load(input); }
        var definitions = binder(properties).bind("jia.agent.task-pricing", Bindable.of(AssigneeQuoteRoutes.Properties.class)).get();
        var routes = new AssigneeQuoteRoutes(definitions);
        var pricing = catalog(properties);
        var expectedAgents = Set.of("jyt-jiafewnnv58ec2379c-linchong", "jyt-jiafewnnv58ec2379c-wuyong", "jyt-jiafewnnv58ec2379c-lujunyi");
        check(definitions.routes().size() == expectedAgents.size() * Workload.Kind.values().length, "Incomplete beta route matrix");
        // Tiny requests, ordinary multi-turn work, input-only, output-only, and mixed/multiple deliverables.
        long[][] cases = {{1, 0, 1, 1}, {0, 1, 1, 1}, {10000, 1000, 1, 2}, {10000, 1000, 7, 2}, {20000, 5000, 2, 4}};
        int quotations = 0;
        for (var agent : expectedAgents) for (var kind : Workload.Kind.values()) {
            var route = routes.find(agent, kind);
            check(route != null, "Missing route: " + agent + "/" + kind);
            check(route.model().equals("gpt-6-luna"), "Unconfirmed model");
            check(route.tools().isEmpty(), "This beta token tariff does not authorize paid tools");
            for (var test : cases) {
                var work = route.workload(new Workload(kind, test[0], test[1], Math.toIntExact(test[2])));
                check(amount(pricing, work, route.modelKey()) == test[3], "Incorrect whole-task/ceiling price for " + agent + "/" + kind);
                quotations++;
            }
        }
        check(routes.find("unregistered-agent", Workload.Kind.MEDIA) == null, "Do not invent an unknown model/channel");
        var route = definitions.routes().getFirst();
        var plain = route.workload(new Workload(Workload.Kind.MEDIA, 10000, 1000, 1));
        unavailable(() -> pricing.prepare(plain, new TaskPricingService.ModelKey("unknown", "unknown", "standard")), TaskPricingService.Unavailable.Reason.MODEL_PRICE_MISSING);
        var incomplete = new Properties(); incomplete.putAll(properties);
        incomplete.remove("economy.pricing.models[0].yuan-per-million-tokens.OUTPUT");
        unavailable(() -> catalog(incomplete).prepare(plain, route.modelKey()), TaskPricingService.Unavailable.Reason.TOKEN_PRICE_MISSING);
        var paidTool = new TaskQuoteCalculator.ToolKey("unregistered", "image-generation", "image");
        var withTool = new TaskWorkload("MEDIA", 10000, 1000, 1, Map.of(paidTool, BigDecimal.ONE));
        unavailable(() -> pricing.prepare(withTool, route.modelKey()), TaskPricingService.Unavailable.Reason.TOOL_PRICE_MISSING);
        // Missing paid price does not contaminate the next token-only quotation.
        check(amount(pricing, plain, route.modelKey()) == 2, "Paid price gap contaminated token-only quote");
        System.out.println("PASS: " + expectedAgents.size() + " agents x " + Workload.Kind.values().length + " kinds; " + quotations + " exact token/ceil quotations; unknown route/model, incomplete token price and unpaid tool boundaries; no model or DB calls");
    }
}
