def optimize(inputFile,outputFile):
    import pandas as pd
    from gurobipy import Model, GRB
    prefs=pd.read_excel(inputFile,header=[0,1,2],sheet_name='Preferences',index_col=0)
    names=prefs.index
    shifts=prefs.columns
    shift_id=shifts.get_level_values(2)
    prefs.columns=shift_id


    I = names
    J = shift_id
    Jw = {}
    t = 0
    for i in range(0,len(J),21):
        t+=1
        ub = i + 21
        Jw[t] = range(i,ub)

    ### Probably useless code
    shift_day = []
    shift_d=shifts.get_level_values(0)
    for i in range (0,len(J),3):
        shift_day.append(str(shift_d[i])[:10])
    ### Night shifts
    N= []
    for n in range(2,len(J),3):
        N.append(n)

    requirments=pd.read_excel(inputFile,sheet_name='Requirements',index_col=0).iloc[:,2]

    Jd = {}
    t = 0
    for i in range(0,len(J),3):
        ub = i + 3
        Jd[shift_day[t]] = range(i,ub)
        t+=1

    P = prefs
    mod = Model()
    x = mod.addVars(I,J,vtype=GRB.BINARY, lb=0,name='x')
    ub1 = mod.addVar(vtype=GRB.INTEGER, lb=0)
    lb1 = mod.addVar(vtype=GRB.INTEGER, lb=0)
    ub2 = mod.addVar(vtype=GRB.INTEGER, lb=0)
    lb2 = mod.addVar(vtype=GRB.INTEGER, lb=0)
    mod.setObjective(sum(P.loc[i,j]*x[i,j] for i in I for j in J) - 100*(ub1-lb1) - 150*(ub2-lb2),sense=GRB.MAXIMIZE)
    for j in J: ### fulfil shift requirements
        mod.addConstr(sum(x[i,j] for i in I) == requirments.loc[j])
    for i in I: ### pref 0 == no schedule
        for j in J:
            mod.addConstr(x[i,j] <= P.loc[i,j],name='x')
    ### every day <= 1
    for i in I:
        for jd in Jd.keys():
            mod.addConstr(sum(x[i,j] for j in Jd[jd]) <= 1,name='x')
    ### every week <= 6
    for i in I:
        for jw in Jw.keys():
            mod.addConstr(sum(x[i,j] for j in Jw[jw]) <= 6,name='x')
    for i in I:
        for n in N:
            if n < len(J)-1:
                mod.addConstr(x[i,n-2] <= (1-x[i,n]))
                mod.addConstr(x[i,n-1] <= (1-x[i,n]))
                mod.addConstr(x[i,n+1] <= (1-x[i,n]))
                mod.addConstr(x[i,n+2] <= (1-x[i,n]))
            else:
                mod.addConstr(x[i,n-2] <= (1-x[i,n]))
                mod.addConstr(x[i,n-1] <= (1-x[i,n]))

    ### shift inequality
    for i in I:
        mod.addConstr(sum(x[i,j] for j in J)<=ub1)
        mod.addConstr(sum(x[i,j] for j in J)>=lb1)

    ### night inequality
    for i in I:
        mod.addConstr(sum(x[i,n] for n in N)<=ub2)
        mod.addConstr(sum(x[i,n] for n in N)>=lb2)




    mod.optimize()
    schedule=pd.DataFrame('',index=names,columns=shift_id)
    for i in I:
        for j in J:
            if x[i,j].x:
                schedule.loc[i,j]=1
    schedule.columns=shifts


    df = pd.DataFrame('',index = ['Obejective','Total preference score','Shift inequality','Night inequality'],columns=['Value'])
    df.iloc[0,0] = mod.objVal
    df.iloc[1,0] = sum(x[i,j].x * P.loc[i,j] for i in I for j in J)
    df.iloc[2,0] = ub1.x-lb1.x
    df.iloc[3,0] = ub2.x-lb2.x


    writer=pd.ExcelWriter(outputFile)
    schedule.to_excel(writer,sheet_name='Schedule')
    df.to_excel(writer,sheet_name='Summary')
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
