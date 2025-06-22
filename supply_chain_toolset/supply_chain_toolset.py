
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, List, Any
from neo4j import GraphDatabase
import os

app = FastAPI()

@app.get("/")
def health_check():
    return {"status": "ok"}

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

def run_cypher(query: str, parameters: dict = {}) -> List[Dict[str, Any]]:
    try:
        with driver.session() as session:
            result = session.run(query, parameters)
            return [record.data() for record in result]
    except Exception as e:
        return [{"error": str(e)}]

class SKURequest(BaseModel):
    sku: str

class CypherRequest(BaseModel):
    query: str
    parameters: dict = {}

class DescriptionRequest(BaseModel):
    description: str

@app.post("/tools/trace_supply_path")
def trace_supply_path(request: DescriptionRequest):
    query = '''
    MATCH (prod:Product)
    WHERE toLower(prod.description) CONTAINS toLower($description)
    WITH prod LIMIT 1
    MATCH path = (sup:Suppliers)-[:SUPPLIES_RM]->(rm:RM)-[:PRODUCT_FLOW*1..8]->(prod)-[:DISTRIBUTED_BY]->(dist:Distributor)
    WITH path LIMIT 20
    WITH nodes(path) AS ns, relationships(path) AS rs
    WITH range(0, size(rs)-1) AS idxs, ns, rs
    RETURN [i IN idxs | {
    from: {
        type: labels(ns[i])[0],
        name: coalesce(ns[i].companyName, ns[i].description, 'Unknown'),
        location: coalesce(ns[i].location, 'N/A'),
        properties: properties(ns[i])
    },
    relationship: {
        type: type(rs[i]),
        properties: properties(rs[i])
    },
    to: {
        type: labels(ns[i+1])[0],
        name: coalesce(ns[i+1].companyName, ns[i+1].description, 'Unknown'),
        location: coalesce(ns[i+1].location, 'N/A'),
        properties: properties(ns[i+1])
    }
    }] AS steps
    '''
    return run_cypher(query, {"description": request.description})


@app.post("/tools/dependency_chain")
def dependency_chain(request: DescriptionRequest):
    query = '''
    MATCH (prod:Product)
    WHERE toLower(prod.description) CONTAINS toLower($description)
    WITH prod LIMIT 1
    MATCH path = (sup:Suppliers)-[:SUPPLIES_RM]->(rm:RM)-[:PRODUCT_FLOW*1..8]->(prod)-[:DISTRIBUTED_BY]->(dist:Distributor)
    WITH path LIMIT 20
    WITH nodes(path) AS ns, relationships(path) AS rs
    WITH range(0, size(rs)-1) AS idxs, ns, rs
    RETURN [i IN idxs | {
    from: {
        type: labels(ns[i])[0],
        name: coalesce(ns[i].companyName, ns[i].description, 'Unknown'),
        location: coalesce(ns[i].location, 'N/A'),
        properties: properties(ns[i])
    },
    relationship: {
        type: type(rs[i]),
        properties: properties(rs[i])
    },
    to: {
        type: labels(ns[i+1])[0],
        name: coalesce(ns[i+1].companyName, ns[i+1].description, 'Unknown'),
        location: coalesce(ns[i+1].location, 'N/A'),
        properties: properties(ns[i+1])
    }
    }] AS steps
    '''
    return run_cypher(query, {"description": request.description})



# @app.post("/tools/dependency_chain")
# def dependency_chain(request: DescriptionRequest):
#     query = '''
#     MATCH path = (sup:Suppliers)-[:SUPPLIES_RM]->(rm:RM)-[:PRODUCT_FLOW*1..8]->(prod:Product)-[:DISTRIBUTED_BY]->(dist:Distributor)
#     WHERE toLower(prod.description) CONTAINS toLower($description)
#     WITH path
#     LIMIT 40
#     WITH nodes(path) as path_nodes, relationships(path) as path_rels
#     RETURN
#         [n in path_nodes | {name: coalesce(n.globalBrand, n.description), brand: n.globalBrand,  form:n.form, package: n.package,  material: n.materialType, labels: labels(n), location: n.location}] AS nodes,
#         [r in path_rels | {type: type(r), package: r.package, form: r.form, demandQnty: r.demandQty, market: r.market}] AS relationships

#     '''
#     return run_cypher(query, {"description": request.description})


# @app.post("/tools/dependency_chain")
# def dependency_chain(request: DescriptionRequest) -> Dict:
#     query = '''
#     MATCH path = (sup:Suppliers)-[:SUPPLIES_RM]->(rm:RM)-[:PRODUCT_FLOW*]->(prod:Product)-[:DISTRIBUTED_BY]->(dist:Distributor)
#     WHERE toLower(prod.description) CONTAINS toLower($description)
#     WITH nodes(path) AS ns, relationships(path) AS rs
#     WITH [n IN ns | apoc.map.merge(properties(n), {labels: labels(n)})] AS nodes,
#          [r IN rs | apoc.map.merge(properties(r), {type: type(r)})] AS relationships
#     RETURN nodes, relationships
#     '''
#     return run_cypher(query, {"description": request.description})

@app.get("/tools/find_single_supplier_risks")
def find_single_supplier_risks() -> List[Dict]:
    query = '''
    MATCH (rm:RM)<-[:SUPPLIES_RM]-(sup:Suppliers)
    WITH rm, COUNT(sup) AS supplierCount
    WHERE supplierCount = 1
    RETURN rm.productSKU AS rawMaterial_SKU, 
       rm.globalBrand AS Raw_Material, rm.location AS Location,
       supplierCount
    LIMIT 50
    '''
    return run_cypher(query)

@app.post("/tools/run_cypher")
def run_cypher_tool(req: CypherRequest):
    return run_cypher(req.query, req.parameters)

@app.get("/tools/top_suppliers_by_product_count")
def top_suppliers():
    query = '''
    MATCH (s:Suppliers)-[:SUPPLIES_RM]->(:RM)-[:PRODUCT_FLOW*1..5]->(p:Product)
    RETURN s.companyName AS supplier, count(DISTINCT p) AS product_count
    ORDER BY product_count DESC LIMIT 50
    '''
    return run_cypher(query)


@app.post("/tools/top_suppliers_for_product")
def top_suppliers_for_product(request: DescriptionRequest):
    query = '''
    MATCH (s:Suppliers)-[:SUPPLIES_RM]->(:RM)-[:PRODUCT_FLOW*1..5]->(p:Product)
    WHERE toLower(p.description) CONTAINS toLower($description)
    RETURN s.companyName AS supplier, count(DISTINCT p) AS product_count
    ORDER BY product_count DESC LIMIT 50
    '''
    return run_cypher(query, {"description": request.description})

@app.get("/tools/raw_materials_by_supplier_count")
def raw_materials_by_suppliers():
    query = '''
    MATCH (rm:RM)<-[:SUPPLIES_RM]-(sup:Suppliers)
    WITH rm, COUNT(sup) AS supplierCount
    WHERE supplierCount = 1
    RETURN 
        rm.productSKU AS rawMaterial_SKU, 
        rm.globalBrand AS Raw_Material, 
        rm.location AS Location,
        supplierCount AS SupplierRisk
    LIMIT 50
    '''
    return run_cypher(query)

@app.get("/tools/api_dependency_risk")
def api_dependency_risk():
    query = '''
    MATCH (api:API)-[:PRODUCT_FLOW]->(dp:DP)
    WITH api, COUNT(dp) AS productCount
    WHERE productCount > 4 
    RETURN api.productSKU AS apiSKU, 
       api.globalBrand AS apiName, 
       productCount
    ORDER BY productCount DESC
    '''
    return run_cypher(query)

@app.post("/tools/distributors_for_product")
def distributors_for_product(request: DescriptionRequest):
    query = '''
    MATCH (p:Product)-[:DISTRIBUTED_BY]->(d:Distributor)
    WHERE toLower(p.description) CONTAINS toLower($description)
    RETURN DISTINCT d {.*}
    '''
    return run_cypher(query, {"description": request.description})


@app.post("/tools/logistics_optimization")
def logistics_optimization(request: DescriptionRequest):
    query = '''
    MATCH (fg:FG:Product WHERE  toLower(fg.globalBrand) CONTAINS toLower($description))
    WHERE NOT EXISTS {
      MATCH (fg)-[pf:PRODUCT_FLOW WHERE toLower(pf.globalBrand) CONTAINS toLower($description)
      ]->(:FG)
    }
    WITH fg, count(*) as num
    MATCH p=(fg)-[pf:PRODUCT_FLOW WHERE toLower(pf.globalBrand) CONTAINS toLower($description)
    ]->+(dist:DIST:Product WHERE dist.globalBrand = fg.globalBrand
      AND dist.generation = fg.generation AND dist.strength = fg.strength AND dist.form = fg.form)
    WHERE EXISTS {MATCH (dist)-[:DISTRIBUTED_BY]->(:Distributor)}
    WITH fg,
      REDUCE(loc=[],x in nodes(p)[0..-1] | loc+[split(x.location,"/")[1]]) as countryList,
      REDUCE(loc=[],x in nodes(p)[0..-1] | loc+[x.location]) as locationList,
      REDUCE(loc=[],x in nodes(p) | loc+[x.location]) as fullLocList
    WITH fg, countryList, locationList, fullLocList,
      apoc.coll.dropDuplicateNeighbors(apoc.coll.sort(countryList)) as dedupCountryList,
      apoc.coll.dropDuplicateNeighbors(apoc.coll.sort(locationList)) as dedupLocationList
    WHERE (countryList[0]=countryList[-1] AND size(dedupCountryList)>1)
      OR (locationList[0]=locationList[-1] AND size(dedupLocationList)>1)
    WITH fg, fullLocList,
      (CASE 
        WHEN countryList[0]=countryList[-1] AND size(dedupCountryList)>1 THEN "Cross Border Shipment"
        WHEN locationList[0]=locationList[-1] AND size(dedupLocationList)>1 THEN "Cyclic Movement"
        ELSE null
      END) as costType
    RETURN DISTINCT costType, fg.form as form, fg.generation as gen, fg.strength as strength, fullLocList as LocationPath
    ORDER BY fg.generation, fg.strength
    '''
    return run_cypher(query, {"description": request.description})

@app.get("/tools/get_schema")
def get_schema():
    query = '''
CALL apoc.meta.data()
YIELD label, property, type, other, elementType
RETURN label, property, type, other, elementType
    '''
    return run_cypher(query)

@app.get("/tools")
def list_tools():
    return [
        {
            "name": "trace_supply_path",
            "description": "Traces the full supply path for a product. Requires a 'description' parameter with the product name.",
            "input_schema": {"description": "string"}
        },
        {
            "name": "dependency_chain",
            "description": "Gets the full dependency chain for a product. Requires a 'description' parameter with the product name.",
            "input_schema": {"description": "string"}
        },
        {
            "name": "find_single_supplier_risks",
            "description": "Finds raw materials that are only supplied by a single company. Takes no parameters.",
            "input_schema": None
        },
        {
            "name": "top_suppliers_by_product_count",
            "description": "Lists the top suppliers by product count. Takes no parameters.",
            "input_schema": None
        },
        {
            "name": "top_suppliers_for_product",
            "description": "For a given product, returns the top suppliers ranked by product count. Requires a 'description' parameter.",
            "input_schema": {"description": "string"}
        },
        {
            "name": "raw_materials_by_supplier_count",
            "description": "List raw materials and their number of suppliers. Flags ones with single suppliers.",
            "input_schema": None
        },
        {
            "name": "api_dependency_risk",
            "description": "Identify Active Pharmaceutical Ingredients(APIs) used in 5 or more different DPs.",
            "input_schema": None
        },
        {
            "name": "logistics_optimization",
            "description": "Analyzes shipment logistics to find inefficiencies like cross-border or cyclic delivery routes. Requires a 'description' parameter with the product name.",
            "category": "logistics_optimization"
        },
        
        {
            "name": "distributors_for_product",
            "description": "List distributors for a product using its description.",
            "input_schema": {"description": "string"}
        },
        {
            "name": "run_cypher",
            "description": "Expert tool to execute a custom Cypher query. REQUIRES a 'query' parameter and an optional 'parameters' dictionary.",
            "input_schema": {
                "query": "string",
                "parameters": "dict (optional)"
            }
        },
        {
            "name": "get_schema",
            "description": "Get schema metadata for the current Neo4j database. Takes no parameters.",
            "input_schema": None
        }
    ]

@app.get("/health")
def health_check():
    try:
        with driver.session() as session:
            result = session.run("RETURN 1 AS ok").single()
            return {"status": "ok", "db": result['ok']}
    except Exception as e:
        return {"status": "error", "message": str(e)}