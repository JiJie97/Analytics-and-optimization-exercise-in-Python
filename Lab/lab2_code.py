def optimize(inputFile,outputFile):
    import pandas as pd
    from gurobipy import Model, GRB
    FC = pd.read_excel(inputFile, sheet_name='Fulfilment Centers',index_col=0)
    I = FC.index   ### fulfilment center index
    Q = FC['capacity']   ### capacity at each fulfilment center
    Regions = pd.read_excel(inputFile, sheet_name='Regions',index_col=0)
    J = Regions.index    ### Demand region index
    Distance = pd.read_excel(inputFile, sheet_name='Distances',index_col=0)
    E = Distance
    Items = pd.read_excel(inputFile, sheet_name='Items',index_col=0)
    K = Items.index   ### Items
    W = Items.iloc[:,0]  ### shipping weight
    S = Items.iloc[:,1]   ### storage size
    D = pd.read_excel(inputFile, sheet_name='Demand',index_col=0)
    cap = []
    mod = Model()
    x = mod.addVars(I,J,K, vtype=GRB.CONTINUOUS, lb=0,name='x')
    mod.setObjective(sum(1.38*W.loc[k]*E.loc[j,i]*x[i,j,k] for i in I for j in J for k in K))
    for j in J:
        for k in K:
            mod.addConstr(sum(x[i,j,k] for i in I) == D.loc[k,j])
    for i in I:
        cap.append(mod.addConstr(sum(x[i,j,k]*S.loc[k] for j in J for k in K) <=Q.loc[i]))
    mod.optimize()
    mod.setParam('outputflag',False)
    Summary = pd.DataFrame([mod.objVal], columns=['Objective Value'])
    Solution = []
    for i in I:
        for j in J:
            for k in K:
                if x[i,j,k].x:
                    Solution.append([i,j,k,x[i,j,k].x])
    Solution = pd.DataFrame(Solution, columns=['FC_name','region_ID','item_ID','shipment'])
    cap = pd.Series(cap,index=I)
    cap1 = []
    for i in range(len(I)):
        cap1.append([I[i],cap[i].pi])
    Capacity_constr = pd.DataFrame(cap1,columns=['FC_name','shadow_price'])
    Capacity_constr = Capacity_constr.sort_values('shadow_price',ascending=True)
    writer=pd.ExcelWriter(outputFile)
    pd.DataFrame([mod.objVal],columns=['Objective Value']).to_excel(writer,sheet_name='Summary',index=False)
    Solution.to_excel(writer,sheet_name='Solution',index=False)
    Capacity_constr.to_excel(writer,sheet_name='Capacity Constraints',index=False)
    writer.save()



if __name__=='__main__':
    import sys, os
    if len(sys.argv)!=3:
        print('Correct syntax: python books.py inputFile outputFile')
    else:
        inputFile=sys.argv[1]
        outputFile=sys.argv[2]
        if os.path.exists(inputFile):
            optimize(inputFile,outputFile)
            print(f'Successfully optimized. Results in "{outputFile}"')
        else:
            print(f'File "{inputFile}" not found!')
